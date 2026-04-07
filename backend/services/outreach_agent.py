import json
from datetime import datetime, timedelta

from backend.services.gmail import send_shortlist_email, send_rejection_email
from backend.services.calendar import create_interview_event
from backend.services.firestore_db import (
    list_candidates,
    get_job_description,
    update_candidate_status,
)
from config.settings import settings

import vertexai
vertexai.init(
    project=settings.google_cloud_project_id,
    location=settings.vertex_ai_location,
)

# ✅ Store candidate context for interaction
_outreach_context = {}


# ✅ dynamic slots
def _generate_slots():
    base = datetime.now() + timedelta(days=1)
    return [
        base.replace(hour=10, minute=0).strftime("%A %I:%M %p"),
        base.replace(hour=14, minute=0).strftime("%A %I:%M %p"),
        (base + timedelta(days=1)).replace(hour=11, minute=0).strftime("%A %I:%M %p"),
    ]


# ─────────────────────────────────────────────────────────────
# MAIN OUTREACH
# ─────────────────────────────────────────────────────────────
def run_outreach_for_jd(
    jd_id: str,
    send_shortlist: bool = True,
    send_rejection: bool = False,
    schedule_interviews: bool = True,
) -> dict:

    try:
        candidates = list_candidates(jd_id)
        jd = get_job_description(jd_id)

        results = []

        for c in candidates:
            candidate_id = c.get("candidate_id")
            status = c.get("status")

            print("👤 Processing candidate:", c.get("email"), "| status:", status)

            if status == "Shortlisted":

                if c.get("interview_scheduled"):
                    print("⛔ Already scheduled, skipping:", c.get("email"))
                    continue

                meet_link = ""

                # ❌ DISABLED AUTO SCHEDULING (correct indentation fix)
                # if schedule_interviews:
                #     print("📅 Scheduling interview for:", c.get("email"))
                #
                #     interview_dt = datetime.now() + timedelta(days=2)
                #     interview_dt = interview_dt.replace(hour=10, minute=0)
                #
                #     try:
                #         event = create_interview_event(
                #             candidate_name=c["name"],
                #             candidate_email=c["email"],
                #             interviewer_email=settings.gmail_sender_email,
                #             role_title=jd.get("role_title", "the position"),
                #             start_datetime=interview_dt,
                #         )
                #
                #         meet_link = event.get("hangoutLink", "")
                #         print("✅ Calendar event created:", meet_link)
                #
                #     except Exception as e:
                #         print("❌ Calendar failed:", str(e))

                # ✅ 2. Store context for interaction
                _outreach_context[candidate_id] = {
                    "name": c["name"],
                    "email": c["email"],
                    "jd_id": jd_id,
                    "meet_link": meet_link
                }

                # ✅ 3. Send email WITH candidate_id
                if send_shortlist:
                    print("📧 ABOUT TO SEND EMAIL TO:", c.get("email"))

                    slots = _generate_slots()

                    try:
                        send_shortlist_email(
                            candidate_id=candidate_id,
                            candidate_name=c["name"],
                            candidate_email=c["email"],
                            role_title=jd.get("role_title", "the position"),
                            slots=slots,
                            meet_link=meet_link,
                        )

                        print("✅ EMAIL FUNCTION CALLED")

                    except Exception as e:
                        print("❌ EMAIL FAILED:", str(e))

                # ✅ 4. Update status
                update_candidate_status(candidate_id, "Interview Scheduled")
                from backend.services.firestore_db import _get_db

                db = _get_db()
                db.collection("candidates").document(candidate_id).update({
                    "interview_scheduled": True
                })

                results.append({
                    "name": c["name"],
                    "email": c["email"],
                    "meet_link": meet_link
                })

            elif status == "Rejected" and send_rejection:
                print("📧 Sending rejection to:", c.get("email"))

                send_rejection_email(
                    candidate_name=c["name"],
                    candidate_email=c["email"],
                    role_title=jd.get("role_title", "the position"),
                )

        return {
            "success": True,
            "message": f"✅ Outreach completed for {len(results)} candidates",
            "details": results
        }

    except Exception as e:
        print("❌ OUTREACH ERROR:", str(e))
        return {"success": False, "message": str(e)}