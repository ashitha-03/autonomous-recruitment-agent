"""
backend/routers/outreach.py
Outreach API endpoints
"""
from fastapi import APIRouter, HTTPException
from backend.services.outreach_agent import run_outreach_for_jd
from backend.services.gmail import send_shortlist_email, send_rejection_email
from backend.services.firestore_db import list_candidates, get_job_description, update_candidate_status
from pydantic import BaseModel

router = APIRouter(prefix="/outreach", tags=["Outreach"])


class BulkOutreachRequest(BaseModel):
    jd_id: str
    send_shortlist: bool = True
    send_rejection: bool = False
    schedule_interviews: bool = True


class SingleEmailRequest(BaseModel):
    candidate_id: str
    jd_id: str
    email_type: str


# ─────────────────────────────────────────────────────────────
# RUN AGENT
# ─────────────────────────────────────────────────────────────
@router.post("/run-agent")
async def run_outreach_agent(req: BulkOutreachRequest):
    try:
        return run_outreach_for_jd(
            jd_id=req.jd_id,
            send_shortlist=req.send_shortlist,
            send_rejection=req.send_rejection,
            schedule_interviews=req.schedule_interviews,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# SEND SINGLE EMAIL
# ─────────────────────────────────────────────────────────────
@router.post("/send-email")
async def send_single_email(req: SingleEmailRequest):
    try:
        jd = get_job_description(req.jd_id)
        candidates = list_candidates(req.jd_id)

        candidate = next(
            (c for c in candidates if c["candidate_id"] == req.candidate_id),
            None
        )

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        if req.email_type == "shortlist":
            send_shortlist_email(
                candidate["name"],
                candidate["email"],
                jd["role_title"]
            )

        elif req.email_type == "rejection":
            send_rejection_email(
                candidate["name"],
                candidate["email"],
                jd["role_title"]
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid email type")

        return {"message": "Email sent"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# ✅ CANDIDATE RESPONSE
# ─────────────────────────────────────────────────────────────
@router.get("/candidate-response")
async def candidate_response(candidate_id: str, response: str, slot: str = None):

    from backend.services.firestore_db import _get_db
    from backend.services.calendar import create_interview_event
    from config.settings import settings
    from datetime import datetime

    try:
        db = _get_db()
        doc = db.collection("candidates").document(candidate_id).get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate = doc.to_dict()

        # ✅ VALIDATION
        if response == "confirm" and not slot:
            raise HTTPException(status_code=400, detail="Slot required")

        # ✅ PREVENT MULTIPLE CONFIRM
        if candidate.get("selected_slot"):
            return {"message": "Slot already selected. Cannot change."}

        # ── CONFIRM SLOT ─────────────────────────────
        if response == "confirm":

            db.collection("candidates").document(candidate_id).update({
                "status": "Confirmed",
                "selected_slot": slot
            })

            return {"message": f"Interview confirmed for {slot}"}

        # ── RESCHEDULE ───────────────────────────────
        elif response == "reschedule":

            db.collection("candidates").document(candidate_id).update({
                "status": "Reschedule Requested",
                "selected_slot": None   # ✅ clear slot
            })

            return {"message": "Reschedule requested"}

        # ── DECLINE ─────────────────────────────────
        elif response == "not_interested":

            db.collection("candidates").document(candidate_id).update({
                "status": "Declined",
                "selected_slot": None   # ✅ clear slot
            })

            return {"message": "Candidate declined"}

        return {"message": "Invalid response"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))