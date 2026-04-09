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

_outreach_context = {}


def _generate_slots():
    base = datetime.now() + timedelta(days=1)
    return [
        base.replace(hour=10, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        base.replace(hour=14, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        (base + timedelta(days=1)).replace(hour=11, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
    ]


def _has_real_email(email: str) -> bool:
    """Returns False for LinkedIn placeholder emails."""
    if not email:
        return False
    if "noemail.com" in email:
        return False
    if email.startswith("linkedin_"):
        return False
    return True


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
        skipped_linkedin = 0
        skipped_already_sent = 0

        for c in candidates:
            candidate_id = c.get("candidate_id")
            status = c.get("status")
            email = c.get("email", "")

            print(f"👤 Processing: {email} | status: {status} | source: {c.get('source')}")

            # ✅ SKIP LinkedIn candidates — they have no real email
            if not _has_real_email(email):
                print(f"⛔ Skipping LinkedIn candidate (no real email): {c.get('name')}")
                skipped_linkedin += 1
                continue

            if status == "Shortlisted":

                # ✅ SKIP if already sent (email_sent flag OR interview_scheduled)
                if c.get("email_sent") or c.get("interview_scheduled"):
                    print(f"⛔ Already contacted, skipping: {email}")
                    skipped_already_sent += 1
                    continue

                meet_link = ""

                # ✅ Store context
                _outreach_context[candidate_id] = {
                    "name": c["name"],
                    "email": email,
                    "jd_id": jd_id,
                    "meet_link": meet_link,
                }

                # ✅ Send shortlist email
                if send_shortlist:
                    print(f"📧 Sending shortlist email to: {email}")
                    slots = _generate_slots()

                    try:
                        send_shortlist_email(
                            candidate_id=candidate_id,
                            candidate_name=c["name"],
                            candidate_email=email,
                            role_title=jd.get("role_title", "the position"),
                            slots=slots,
                            meet_link=meet_link,
                        )

                        # ✅ Mark as email_sent so it won't be sent again
                        from backend.services.firestore_db import _get_db
                        _get_db().collection("candidates").document(candidate_id).update({
                            "email_sent": True
                        })

                        print(f"✅ Email sent to: {email}")

                    except Exception as e:
                        print(f"❌ Email failed for {email}: {str(e)}")

                results.append({
                    "name": c["name"],
                    "email": email,
                    "meet_link": meet_link,
                })

            elif status == "Rejected" and send_rejection:

                # ✅ Skip fake emails for rejection too
                print(f"📧 Sending rejection to: {email}")
                try:
                    send_rejection_email(
                        candidate_name=c["name"],
                        candidate_email=email,
                        role_title=jd.get("role_title", "the position"),
                    )
                except Exception as e:
                    print(f"❌ Rejection email failed: {str(e)}")

        summary = f"✅ Outreach completed: {len(results)} emails sent"
        if skipped_already_sent:
            summary += f", {skipped_already_sent} already contacted (skipped)"
        if skipped_linkedin:
            summary += f", {skipped_linkedin} LinkedIn candidates skipped (no real email)"

        return {
            "success": True,
            "message": summary,
            "details": results,
        }

    except Exception as e:
        print(f"❌ OUTREACH ERROR: {str(e)}")
        return {"success": False, "message": str(e)}