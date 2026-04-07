import smtplib
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


def _send_email_smtp(to_email: str, subject: str, html_body: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.gmail_sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        print("📧 Connecting to SMTP...")

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login(
            settings.gmail_sender_email,
            settings.gmail_app_password
        )

        server.sendmail(
            settings.gmail_sender_email,
            to_email,
            msg.as_string()
        )

        server.quit()

        print("✅ EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("❌ SMTP EMAIL FAILED:", str(e))


# ✅ SHORTLIST EMAIL
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


# ✅ REJECTION EMAIL
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