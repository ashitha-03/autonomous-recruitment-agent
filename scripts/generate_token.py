from google_auth_oauthlib.flow import InstalledAppFlow
import pickle, os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

flow = InstalledAppFlow.from_client_secrets_file(
    "config/oauth_client.json",
    scopes=SCOPES
)

creds = flow.run_local_server(port=0)

with open("config/token.pickle", "wb") as f:
    pickle.dump(creds, f)

print("✅ token.pickle created successfully!")