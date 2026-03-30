"""
backend/models/schemas.py
All Pydantic data models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class JDGenerateRequest(BaseModel):
    role_title: str
    department: str
    experience_years: int = 3
    skills_hint: Optional[str] = None
    company_name: Optional[str] = None
    work_mode: str = "Hybrid"
    location: Optional[str] = None
    employment_type: Optional[str] = "Full-time"
    salary_range: Optional[str] = None


class JobDescription(BaseModel):
    jd_id: Optional[str] = None
    role_title: str
    department: str
    summary: Optional[str] = ""
    responsibilities: Optional[List[str]] = []
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    experience_years: int
    work_mode: Optional[str] = ""
    location: Optional[str] = None
    employment_type: Optional[str] = "Full-time"
    salary_range: Optional[str] = None
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = []
    education: Optional[str] = None
    resume_text: Optional[str] = None


class CandidateCreate(CandidateBase):
    jd_id: str


class CandidateScore(BaseModel):
    candidate_id: str
    jd_id: str
    overall_score: float
    skills_match: float
    experience_match: float
    education_match: float
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    ai_summary: str
    recommendation: str
    rejection_reason: Optional[str] = None
    scored_at: Optional[datetime] = None


class Candidate(CandidateBase):
    candidate_id: Optional[str] = None
    jd_id: Optional[str] = None
    score: Optional[CandidateScore] = None
    status: str = "Applied"
    source: str = "Resume Upload"


class LinkedInScrapeRequest(BaseModel):
    search_keywords: str
    max_profiles: int = 20
    jd_id: str


class InterviewEmailRequest(BaseModel):
    candidate_id: str
    jd_id: str
    interview_datetime: datetime
    meeting_link: Optional[str] = None
    interviewer_name: str


class ScheduleInterviewRequest(BaseModel):
    candidate_id: str
    jd_id: str
    proposed_slots: List[datetime]
    interviewer_email: str