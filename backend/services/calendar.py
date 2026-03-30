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
    Creates OFFLINE interview event (NO Google Meet)
    """

    service = _get_calendar_service()
    end_datetime = start_datetime + timedelta(minutes=60)

    event = {
        "summary": f"Interview: {candidate_name} – {role_title}",
        "description": description or f"Offline interview for {role_title}",
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

        # ✅ THIS IS THE IMPORTANT PART
        "location": f"{role_title} Interview – {candidate_name} | Office - Kochi",

        # ❌ REMOVED conferenceData (no Meet link)
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event,
        sendUpdates="all",   # sends email invite
    ).execute()

    return created_event