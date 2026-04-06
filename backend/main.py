"""
backend/main.py
FastAPI entry
"""
import os
from config.settings import settings
if settings.google_application_credentials:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import jd, resume, candidates, auth, linkedin, outreach
from config.settings import settings

app = FastAPI(
    title="Autonomous Recruitment Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jd.router)
app.include_router(resume.router)
app.include_router(candidates.router)
app.include_router(linkedin.router)
app.include_router(outreach.router)


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test-db")
def test_db():
    from backend.services.firestore_db import _get_db
    db = _get_db()
    db.collection("test").document("1").set({"ok": True})
    return {"message": "Firestore working"}