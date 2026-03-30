"""
backend/utils/auth.py
Google authentication helpers
"""
import pickle
from pathlib import Path
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Minimal scopes (only what you need)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

SERVICE_ACCOUNT_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
]

TOKEN_PICKLE = "config/token.pickle"
CREDENTIALS_FILE = "config/credentials.json"
OAUTH_CLIENT_FILE = "config/oauth_client.json"


def get_service_account_credentials():
    """Used for Vertex AI"""
    return service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SERVICE_ACCOUNT_SCOPES,
    )


def get_oauth_credentials():
    """Used for Gmail + Calendar"""
    creds = None

    # Load token
    if Path(TOKEN_PICKLE).exists():
        with open(TOKEN_PICKLE, "rb") as f:
            creds = pickle.load(f)

    # Refresh or login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PICKLE, "wb") as f:
            pickle.dump(creds, f)

    return creds