import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
from datetime import datetime, timedelta


# 🔥 Dynamic slots
def _generate_slots():
    base = datetime.now() + timedelta(days=1)

    return [
        base.replace(hour=10, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        base.replace(hour=14, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        (base + timedelta(days=1)).replace(hour=11, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
    ]


# ✅ NEW EMAIL SENDER (API BASED)
def _send_email_smtp(to_email: str, subject: str, html_body: str):
    try:
        print("📧 Sending via RESEND API...")

        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            },
        )

        print("📧 RESPONSE:", response.status_code, response.text)

        # ✅ FIXED INDENTATION
        if response.status_code != 200:
            raise Exception(f"Email failed: {response.text}")

    except Exception as e:
        print("❌ EMAIL FAILED:", str(e))
        raise e   # 🔥 IMPORTANT (don’t remove)


# ✅ SHORTLIST EMAIL (UNCHANGED LOGIC)
def send_shortlist_email(candidate_id, candidate_name, candidate_email, role_title, slots=None, meet_link=None, company_name="10xDS-Exponetial Digital Solutions"):

    if not slots:
        slots = _generate_slots()

    subject = f"Interview Scheduled – {role_title} at {company_name}"

    slots_html = "".join([f"<li>{slot}</li>" for slot in slots])

    BASE_URL = "https://autonomous-recruitment-agent-iorz.onrender.com/outreach/candidate-response"

    actions_html = f"""
    <p><strong>Select your preferred interview slot:</strong></p>
    <ul>
        {"".join([
            f"<li><a href='{BASE_URL}?candidate_id={candidate_id}&response=confirm&slot={slot}'>{slot}</a></li>"
            for slot in slots
        ])}
    </ul>

    <p>Or:</p>
    <ul>
        <li><a href="{BASE_URL}?candidate_id={candidate_id}&response=reschedule">Request Reschedule</a></li>
        <li><a href="{BASE_URL}?candidate_id={candidate_id}&response=not_interested">Decline</a></li>
    </ul>
    """

    meet_html = f"""
    <p><strong>Meeting Link:</strong> <a href='{meet_link}'>{meet_link}</a></p>
    """ if meet_link else ""

    body = f"""
    <html><body>
    <p>Dear {candidate_name},</p>

    <p>You have been <strong>shortlisted</strong> for <strong>{role_title}</strong>.</p>

    <ul>{slots_html}</ul>

    {meet_html}

    {actions_html}

    <p>Best regards,<br/>HR Team – {company_name}</p>
    </body></html>
    """

    _send_email_smtp(candidate_email, subject, body)


# ✅ REJECTION EMAIL (UNCHANGED)
def send_rejection_email(candidate_name, candidate_email, role_title, company_name="Our Company"):

    subject = f"Application Update – {role_title} at {company_name}"

    body = f"""
    <html><body>
    <p>Dear {candidate_name},</p>
    <p>We regret to inform you that you were not selected.</p>
    <p>Best wishes.</p>
    </body></html>
    """

    _send_email_smtp(candidate_email, subject, body)