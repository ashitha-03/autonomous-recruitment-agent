"""
backend/services/firestore_db.py
All database operations using Firebase Firestore.
Database: ashitha-month2
"""
import firebase_admin
from firebase_admin import credentials, firestore
from backend.models.schemas import Candidate, JobDescription, CandidateScore
import uuid
from datetime import datetime


def _get_db():
    """Returns Firestore client with correct database name."""
    if not firebase_admin._apps:
        cred = credentials.Certificate("config/credentials.json")
        firebase_admin.initialize_app(cred)
    return firestore.client(database_id='ashitha-month2')


# ─── Job Description Operations ───────────────────────────────────────────────

def save_job_description(jd: JobDescription) -> str:
    db = _get_db()
    jd_id = jd.jd_id or str(uuid.uuid4())
    data = {
        "jd_id": jd_id,
        "role_title": jd.role_title,
        "department": jd.department or "",
        "summary": jd.summary or "",
        "responsibilities": " | ".join(jd.responsibilities or []),
        "required_skills": ", ".join(jd.required_skills or []),
        "preferred_skills": ", ".join(jd.preferred_skills or []),
        "experience_years": jd.experience_years or 0,
        "work_mode": jd.work_mode or "",
        "location": jd.location or "",
        "employment_type": jd.employment_type or "Full-time",
        "salary_range": jd.salary_range or "",
        "company_name": jd.company_name or "",
        "created_at": datetime.utcnow().isoformat(),
    }
    db.collection("job_descriptions").document(jd_id).set(data)
    return jd_id


def get_job_description(jd_id: str) -> dict | None:
    db = _get_db()
    doc = db.collection("job_descriptions").document(jd_id).get()
    return doc.to_dict() if doc.exists else None


def list_job_descriptions() -> list[dict]:
    db = _get_db()
    docs = db.collection("job_descriptions").order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).stream()
    return [doc.to_dict() for doc in docs]


def delete_job_description(jd_id: str):
    db = _get_db()
    db.collection("job_descriptions").document(jd_id).delete()


def update_job_description(jd_id: str, data: dict):
    db = _get_db()
    db.collection("job_descriptions").document(jd_id).update(data)


# ─── Candidate Operations ─────────────────────────────────────────────────────

def save_candidate(candidate: Candidate, score: CandidateScore | None = None) -> str:
    db = _get_db()
    candidate_id = candidate.candidate_id or str(uuid.uuid4())
    data = {
        "candidate_id": candidate_id,
        "jd_id": candidate.jd_id or None,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "linkedin_url": candidate.linkedin_url,
        "current_title": candidate.current_title,
        "years_experience": candidate.years_experience,
        "skills": ", ".join(candidate.skills) if candidate.skills else "",
        "education": candidate.education,
        "status": candidate.status,
        "source": candidate.source,
        "resume_text": candidate.resume_text,
        "overall_score": score.overall_score if score else None,
        "skills_match": score.skills_match if score else None,
        "experience_match": score.experience_match if score else None,
        "education_match": score.education_match if score else None,
        "recommendation": score.recommendation if score else None,
        "ai_summary": score.ai_summary if score else None,
        "rejection_reason": score.rejection_reason if score else None,
        "matched_skills": ", ".join(score.matched_skills) if score and score.matched_skills else None,
        "missing_skills": ", ".join(score.missing_skills) if score and score.missing_skills else None,
        "scored_at": score.scored_at.isoformat() if score and score.scored_at else None,
        "created_at": datetime.utcnow().isoformat(),
    }
    db.collection("candidates").document(candidate_id).set(data)
    return candidate_id


def candidate_exists(email: str, jd_id: str) -> bool:
    db = _get_db()
    import hashlib
    doc_id = hashlib.md5(f"{email}_{jd_id}".encode()).hexdigest()
    doc = db.collection("candidates").document(doc_id).get()
    return doc.exists


def list_candidates(jd_id: str | None = None) -> list[dict]:
    db = _get_db()
    query = db.collection("candidates")
    if jd_id:
        query = query.where("jd_id", "==", jd_id)
    docs = query.stream()
    candidates = [doc.to_dict() for doc in docs]
    candidates.sort(key=lambda x: float(x.get("overall_score") or 0), reverse=True)
    return candidates


def update_candidate_status(candidate_id: str, new_status: str):
    db = _get_db()
    db.collection("candidates").document(candidate_id).update({"status": new_status})