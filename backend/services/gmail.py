import os
import requests
from config.settings import settings
from datetime import datetime, timedelta


def _generate_slots():
    base = datetime.now() + timedelta(days=1)
    return [
        base.replace(hour=10, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        base.replace(hour=14, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
        (base + timedelta(days=1)).replace(hour=11, minute=0).strftime("%A, %d %B %Y at %I:%M %p"),
    ]


def _get_token_path() -> str:
    """Find token.pickle — searches from current working directory (project root)."""
    # When running uvicorn from project root, cwd is the project root
    cwd_token = os.path.join(os.getcwd(), "config", "token.pickle")
    if os.path.exists(cwd_token):
        return cwd_token
    return None


def _is_local() -> bool:
    """True if token.pickle exists = local dev."""
    path = _get_token_path()
    result = path is not None
    print(f"🔍 _is_local={result}, token_path={path}")
    return result


# ── LOCAL: Gmail OAuth ────────────────────────────────────────────────────────
def _send_via_gmail_oauth(to_email: str, subject: str, html_body: str):
    import pickle
    import base64
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from googleapiclient.discovery import build

    token_path = _get_token_path()
    print(f"📧 Sending via Gmail OAuth | token: {token_path}")

    with open(token_path, "rb") as f:
        creds = pickle.load(f)

    # ✅ Refresh if expired
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        # Save refreshed token
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    service = build("gmail", "v1", credentials=creds)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.gmail_sender_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"✅ Gmail OAuth email sent to: {to_email}")


# ── DEPLOYMENT: SendGrid ──────────────────────────────────────────────────────
def _send_via_sendgrid(to_email: str, subject: str, html_body: str):
    print("📧 Sending via SendGrid...")

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": settings.gmail_sender_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_body}],
        },
        timeout=10,
    )

    print("📧 SendGrid RESPONSE:", response.status_code, response.text)

    if response.status_code not in [200, 202]:
        raise Exception(f"SendGrid failed: {response.text}")

    print(f"✅ SendGrid email sent to: {to_email}")


# ── SMART DISPATCHER ──────────────────────────────────────────────────────────
def _send_email(to_email: str, subject: str, html_body: str):
    try:
        if _is_local():
            _send_via_gmail_oauth(to_email, subject, html_body)
        else:
            _send_via_sendgrid(to_email, subject, html_body)
    except Exception as e:
        print(f"❌ EMAIL FAILED: {str(e)}")
        raise e


# ── SHORTLIST EMAIL ───────────────────────────────────────────────────────────
def send_shortlist_email(
    candidate_id,
    candidate_name,
    candidate_email,
    role_title,
    slots=None,
    meet_link=None,
    company_name="10xDS-Exponential Digital Solutions",
):
    if not slots:
        slots = _generate_slots()

    subject = f"Interview Scheduled – {role_title} at {company_name}"
    slots_html = "".join([f"<li>{slot}</li>" for slot in slots])

    BASE_URL = f"{settings.backend_url}/outreach/candidate-response"

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

    meet_html = f"<p><strong>Meeting Link:</strong> <a href='{meet_link}'>{meet_link}</a></p>" if meet_link else ""

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

    _send_email(candidate_email, subject, body)


# ── REJECTION EMAIL ───────────────────────────────────────────────────────────
def send_rejection_email(candidate_name, candidate_email, role_title, company_name="Our Company"):
    subject = f"Application Update – {role_title} at {company_name}"
    body = f"""
    <html><body>
    <p>Dear {candidate_name},</p>
    <p>We regret to inform you that you were not selected for <strong>{role_title}</strong>.</p>
    <p>We appreciate your interest and wish you all the best.</p>
    <p>Best wishes,<br/>HR Team – {company_name}</p>
    </body></html>
    """
    _send_email(candidate_email, subject, body)