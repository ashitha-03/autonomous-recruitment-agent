import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from backend.utils.auth import get_oauth_credentials
from config.settings import settings
from datetime import datetime, timedelta


def _get_gmail_service():
    creds = get_oauth_credentials()
    return build("gmail", "v1", credentials=creds)


def _create_message(to: str, subject: str, html_body: str) -> dict:
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.gmail_sender_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


# 🔥 Dynamic slots
def _generate_slots():
    base = datetime.now() + timedelta(days=1)

    return [
        base.replace(hour=10, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        base.replace(hour=14, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        (base + timedelta(days=1)).replace(hour=11, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
    ]


# ✅ FIXED FUNCTION
def send_shortlist_email(candidate_id, candidate_name, candidate_email, role_title, slots=None, meet_link=None, company_name="10xDS-Exponetial Digital Solutions"):

    if not slots:
        slots = _generate_slots()

    subject = f"Interview Scheduled – {role_title} at {company_name}"

    # 🔹 Slot list
    slots_html = "".join([f"<li>{slot}</li>" for slot in slots])

    # 🔹 Candidate interaction links
    BASE_URL = "http://localhost:8000/outreach/candidate-response"

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
    # 🔹 Meet link (optional)
    meet_html = f"""
    <p><strong>Meeting Link:</strong> <a href='{meet_link}'>{meet_link}</a></p>
    """ if meet_link else ""

    # 🔹 Email body
    body = f"""
    <html><body>
    <p>Dear {candidate_name},</p>

    <p>We are pleased to inform you that you have been <strong>shortlisted</strong> for the role of <strong>{role_title}</strong> at <strong>{company_name}</strong>.</p>

    <p>Your interview has been <strong>scheduled</strong. Please find the details below:</p>

    <ul>
        {slots_html}
    </ul>

    {meet_html}

    {actions_html}

    <p>If the scheduled timing is not convenient, you may request a reschedule.</p>

    <p>We look forward to speaking with you.</p>

    <p>Best regards,<br/>HR Team – {company_name}</p>
    </body></html>
    """

    service = _get_gmail_service()
    message = _create_message(candidate_email, subject, body)
    return service.users().messages().send(userId="me", body=message).execute()


# ✅ FIXED rejection email
def send_rejection_email(candidate_name, candidate_email, role_title, company_name="Our Company"):
    subject = f"Application Update – {role_title} at {company_name}"

    body = f"""
    <html><body>
    <p>Dear {candidate_name},</p>
    <p>Thank you for applying for <strong>{role_title}</strong>.</p>
    <p>We regret to inform you that you were not selected.</p>
    <p>Best wishes for your future.</p>
    <p>HR Team – {company_name}</p>
    </body></html>
    """

    service = _get_gmail_service()
    message = _create_message(candidate_email, subject, body)
    return service.users().messages().send(userId="me", body=message).execute()