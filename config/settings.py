"""
config/settings.py
Central configuration
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

# ✅ Find .env at project root regardless of where uvicorn is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):

    # Google Cloud
    google_cloud_project_id: str
    gmail_app_password: Optional[str] = None
    google_application_credentials: Optional[str] = None
    google_credentials_json: Optional[str] = None
    sendgrid_api_key: Optional[str] = None

    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-2.5-flash"
    company_name: str = "Our Company"

    openrouter_api_key: Optional[str] = None
    document_ai_processor_id: str = ""

    # Gmail
    gmail_oauth_client_id: Optional[str] = None
    gmail_oauth_client_secret: Optional[str] = None
    gmail_oauth_redirect_uri: str = "http://localhost:8000/auth/callback"
    gmail_sender_email: Optional[str] = None

    # Calendar
    calendar_id: str = "primary"
    interview_duration_minutes: int = 45

    # LinkedIn
    serp_api_key: Optional[str] = None

    # HR Login
    hr_email: str = "hr@company.com"
    hr_password: str = "hr1234"

    # App
    secret_key: str = "change-me"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ENV_PATH   # ✅ absolute path to .env at project root
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()