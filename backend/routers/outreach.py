"""
backend/routers/outreach.py
Outreach API endpoints
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from backend.services.outreach_agent import run_outreach_for_jd
from backend.services.gmail import send_shortlist_email, send_rejection_email
from backend.services.firestore_db import list_candidates, get_job_description, update_candidate_status
from config.settings import settings
from pydantic import BaseModel
from datetime import datetime

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
                candidate_id=candidate["candidate_id"],
                candidate_name=candidate["name"],
                candidate_email=candidate["email"],
                role_title=jd["role_title"]
            )
        elif req.email_type == "rejection":
            send_rejection_email(
                candidate_name=candidate["name"],
                candidate_email=candidate["email"],
                role_title=jd["role_title"]
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid email type")

        return {"message": "Email sent"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# CANDIDATE RESPONSE
# ─────────────────────────────────────────────────────────────
@router.get("/candidate-response")
async def candidate_response(candidate_id: str, response: str, slot: str = None):

    from backend.services.firestore_db import _get_db
    from backend.services.calendar import create_interview_event
    from datetime import datetime
    import urllib.parse

    try:
        db = _get_db()
        doc = db.collection("candidates").document(candidate_id).get()

        if not doc.exists:
            # ✅ Redirect to frontend with error
            return RedirectResponse(
                url=f"{settings.frontend_url}/confirmed?status=error&message=Candidate+not+found"
            )

        candidate = doc.to_dict()

        # ✅ PREVENT MULTIPLE CONFIRM
        if candidate.get("selected_slot"):
            return RedirectResponse(
                url=f"{settings.frontend_url}/confirmed?status=already&slot={urllib.parse.quote(candidate['selected_slot'])}"
            )

        # ── CONFIRM SLOT ─────────────────────────────────────
        if response == "confirm":
            if not slot:
                return RedirectResponse(
                    url=f"{settings.frontend_url}/confirmed?status=error&message=No+slot+provided"
                )

            # ✅ Parse slot string to datetime
            interview_time = _parse_slot_to_datetime(slot)
            meet_link = ""
            calendar_link = ""

            try:
                event = create_interview_event(
                    candidate_name=candidate["name"],
                    candidate_email=candidate["email"],
                    interviewer_email=settings.gmail_sender_email,
                    role_title=candidate.get("jd_id", "the position"),
                    start_datetime=interview_time,
                )
                meet_link = event.get("hangoutLink", "")
                calendar_link = event.get("htmlLink", "")
                print(f"✅ Meet link: {meet_link}")

            except Exception as e:
                print(f"❌ Calendar failed: {str(e)}")

            # ✅ Update Firestore
            db.collection("candidates").document(candidate_id).update({
                "status": "Interview Scheduled",
                "selected_slot": slot,
                "meet_link": meet_link,
                "calendar_event": calendar_link,
                "interview_scheduled": True,
            })

            # ✅ Redirect to nice frontend confirmation page
            params = urllib.parse.urlencode({
                "status": "confirmed",
                "name": candidate["name"],
                "slot": slot,
                "meet": meet_link,
            })
            return RedirectResponse(url=f"{settings.frontend_url}/confirmed?{params}")

        # ── RESCHEDULE ───────────────────────────────────────
        elif response == "reschedule":
            db.collection("candidates").document(candidate_id).update({
                "status": "Reschedule Requested",
                "selected_slot": None,
            })
            return RedirectResponse(
                url=f"{settings.frontend_url}/confirmed?status=reschedule&name={urllib.parse.quote(candidate['name'])}"
            )

        # ── DECLINE ──────────────────────────────────────────
        elif response == "not_interested":
            db.collection("candidates").document(candidate_id).update({
                "status": "Declined",
                "selected_slot": None,
            })
            return RedirectResponse(
                url=f"{settings.frontend_url}/confirmed?status=declined&name={urllib.parse.quote(candidate['name'])}"
            )

        return RedirectResponse(
            url=f"{settings.frontend_url}/confirmed?status=error&message=Invalid+response"
        )

    except Exception as e:
        print(f"❌ candidate_response error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/confirmed?status=error&message={urllib.parse.quote(str(e))}"
        )


def _parse_slot_to_datetime(slot: str) -> datetime:
    """
    Parses slot string like 'Friday, 11 April 2026 at 10:00 AM' to datetime.
    Falls back to tomorrow 10am if parsing fails.
    """
    from datetime import timedelta
    try:
        # Format: "Friday, 11 April 2026 at 10:00 AM"
        cleaned = slot.replace(" at ", " ")
        dt = datetime.strptime(cleaned, "%A, %d %B %Y %I:%M %p")
        return dt
    except Exception:
        try:
            # Format: "Friday 10:00 AM" (short format)
            now = datetime.now()
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for i, day in enumerate(days):
                if slot.startswith(day):
                    time_part = slot.replace(day, "").strip()
                    t = datetime.strptime(time_part, "%I:%M %p")
                    # Find next occurrence of this weekday
                    current_weekday = now.weekday()
                    target_weekday = i
                    days_ahead = (target_weekday - current_weekday) % 7 or 7
                    target_date = now + timedelta(days=days_ahead)
                    return target_date.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except Exception:
            pass

    # Fallback: tomorrow at 10am
    print(f"⚠️ Could not parse slot '{slot}', using tomorrow 10am")
    return datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)