# backend/services/calendar.py

from googleapiclient.discovery import build
from backend.utils.auth import get_oauth_credentials
from datetime import datetime, timedelta


def _get_calendar_service():
    creds = get_oauth_credentials()
    return build("calendar", "v3", credentials=creds)


def create_interview_event(
    candidate_name: str,
    candidate_email: str,
    interviewer_email: str,
    role_title: str,
    start_datetime: datetime,
    description: str = "",
) -> dict:
    """
    Creates interview event WITH Google Meet link.
    """

    service = _get_calendar_service()
    end_datetime = start_datetime + timedelta(minutes=60)

    event = {
        "summary": f"Interview: {candidate_name} – {role_title}",
        "description": description or f"Interview for {role_title} position.\nCandidate: {candidate_name}",
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "attendees": [
            {"email": candidate_email},
            {"email": interviewer_email},
        ],

        # ✅ Google Meet link
        "conferenceData": {
            "createRequest": {
                "requestId": f"interview-{candidate_name}-{start_datetime.strftime('%Y%m%d%H%M')}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1,  # ✅ Required for Meet link
        sendUpdates="all",         # ✅ Sends email invite to all attendees
    ).execute()

    print(f"✅ Calendar event created: {created_event.get('htmlLink')}")
    print(f"🎥 Meet link: {created_event.get('hangoutLink')}")

    return created_event