# backend/routers/linkedin.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.linkedin import scrape_linkedin_profiles
from backend.services.scorer import score_candidate
from backend.services.firestore_db import save_candidate, get_job_description
from backend.models.schemas import Candidate, JobDescription
import uuid

from backend.services.recruitment_agent import generate_explanation_tool, _context

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])


class LinkedInRequest(BaseModel):
    search_keywords: str
    jd_id: str
    max_profiles: int = 10


def _build_jd(jd_data: dict) -> JobDescription:
    return JobDescription(
        jd_id=jd_data["jd_id"],
        role_title=jd_data["role_title"],
        department=jd_data.get("department", ""),
        summary=jd_data.get("summary", ""),
        responsibilities=(jd_data.get("responsibilities") or "").split(" | "),
        required_skills=[
            s.strip()
            for s in (jd_data.get("required_skills") or "").replace(",", ", ").split(", ")
            if s.strip()
        ],
        preferred_skills=[
            s.strip()
            for s in (jd_data.get("preferred_skills") or "").replace(",", ", ").split(", ")
            if s.strip()
        ],
        experience_years=int(jd_data.get("experience_years") or 0),
        work_mode=jd_data.get("work_mode", ""),
    )


@router.post("/scrape")
async def scrape_and_score(request: LinkedInRequest):

    jd_id = request.jd_id
    search_keywords = request.search_keywords
    max_profiles = request.max_profiles

    # 🔹 Get JD
    jd_data = get_job_description(jd_id)
    if not jd_data:
        raise HTTPException(status_code=404, detail="Job Description not found")

    jd = _build_jd(jd_data)

    # 🔹 Scrape LinkedIn
    try:
        profiles = scrape_linkedin_profiles(search_keywords, jd_id, max_profiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    results = []

    for profile in profiles:

        # ✅ Extract skills safely
        raw_skills = profile.get("skills") or []
        skills = []
        if isinstance(raw_skills, list):
            for s in raw_skills:
                if isinstance(s, dict):
                    skills.append(s.get("name", ""))
                else:
                    skills.append(str(s))

        # ✅ FIX: Always use a valid email
        placeholder_email = f"linkedin_{uuid.uuid4().hex[:8]}@noemail.com"

        candidate = Candidate(
            candidate_id=str(uuid.uuid4()),
            jd_id=jd_id,
            name=profile.get("name", "Unknown"),
            email=placeholder_email,
            phone=None,
            linkedin_url=profile.get("linkedin_url", ""),
            current_title=profile.get("current_title", "")[:100],
            years_experience=_estimate_experience(profile.get("experience", [])),
            skills=skills,
            education=_extract_education(profile.get("education", [])),
            resume_text=f"{profile.get('summary', '')} {' '.join(skills)}",
            status="Sourced",  # LinkedIn = Sourced, not Applied
            source="LinkedIn",
        )

        # 🔹 Score candidate
        score = None
        explanation = None
        try:
            score = score_candidate(candidate, jd)
            score.candidate_id = candidate.candidate_id

            # ✅ Inject into agent context for AI explanation
            _context["candidate"] = candidate
            _context["score"] = score
            _context["jd_data"] = jd_data

            explanation = generate_explanation_tool()
            score.ai_summary = explanation

            # ✅ Same threshold as resume candidates
            if score.overall_score >= 70:
                candidate.status = "Shortlisted"
            elif score.overall_score >= 40:
                candidate.status = "Maybe"
            else:
                candidate.status = "Rejected"

        except Exception as e:
            print(f"⚠️ Scoring/explanation failed for {candidate.name}: {e}")
            candidate.status = "Applied"

        # 🔹 Save to Firestore
        try:
            save_candidate(candidate, score)
        except Exception as e:
            print(f"⚠️ Save failed for {candidate.name}: {e}")

        # 🔹 Append result
        results.append({
            "name": candidate.name,
            "linkedin_url": candidate.linkedin_url,
            "current_title": candidate.current_title,
            "score": score.overall_score if score else 0,
            "recommendation": score.recommendation if score else "N/A",
            "status": candidate.status,
            "matched_skills": score.matched_skills if score else [],
            "missing_skills": score.missing_skills if score else [],
            "ai_summary": explanation,
        })

    return {
        "scraped": len(profiles),
        "processed": len(results),
        "results": results,
        "message": f"✅ Successfully scraped and scored {len(results)} LinkedIn profiles",
    }


def _estimate_experience(experiences: list) -> float:
    return float(min(len(experiences) * 1.5, 15))


def _extract_education(educations: list) -> str:
    if not educations:
        return None
    edu = educations[0]
    if isinstance(edu, dict):
        return f"{edu.get('degree', '')} {edu.get('fieldOfStudy', '')} - {edu.get('schoolName', '')}"
    return str(edu)