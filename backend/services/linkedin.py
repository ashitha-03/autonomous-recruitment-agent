# backend/services/linkedin.py

from config.settings import settings
import requests
import uuid

from backend.services.scorer import score_candidate
from backend.models.schemas import Candidate, JobDescription
from backend.services.firestore_db import get_job_description


def scrape_linkedin_profiles(search_keywords: str, jd_id: str, max_profiles: int = 5):

    print("🔍 Searching via SerpAPI:", search_keywords)
    print("🔑 SERP KEY:", settings.serp_api_key[:10] + "..." if settings.serp_api_key else "MISSING")

    query = f'site:linkedin.com/in "{search_keywords}" -jobs -hiring'

    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": settings.serp_api_key,
        "num": max_profiles,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data:
        raise Exception(f"SerpAPI error: {data['error']}")

    profiles = []

    jd_data = get_job_description(jd_id)

    jd = JobDescription(
        jd_id=jd_data["jd_id"],
        role_title=jd_data["role_title"],
        department="",
        summary="",
        responsibilities=[],
        required_skills=[
            s.strip() for s in (jd_data.get("required_skills") or "").split(",") if s.strip()
        ],
        preferred_skills=[],
        experience_years=0,
        work_mode="",
    )

    for result in data.get("organic_results", [])[:max_profiles]:

        text = result.get("snippet", "").lower()

        # ✅ Simple skill detection
        detected_skills = []
        for skill in ["python", "java", "sql", "react", "aws", "javascript", "typescript",
                      "nodejs", "docker", "kubernetes", "machine learning", "django", "fastapi"]:
            if skill in text:
                detected_skills.append(skill)

        # ✅ FIX: Generate a valid placeholder email (empty string fails validation)
        safe_name = result.get("title", "unknown").lower().replace(" ", "").replace("-", "")[:20]
        placeholder_email = f"linkedin_{uuid.uuid4().hex[:8]}@noemail.com"

        candidate = Candidate(
            candidate_id=f"linkedin_{uuid.uuid4().hex[:12]}",
            jd_id=jd_id,
            name=result.get("title", "Unknown"),
            email=placeholder_email,
            phone=None,
            linkedin_url=result.get("link", ""),
            current_title=result.get("snippet", "")[:100],
            years_experience=0,
            skills=detected_skills,
            education="",
            resume_text=text,
            status="Sourced",  # router will update based on score
            source="LinkedIn",
        )

        try:
            score = score_candidate(candidate, jd)
        except Exception as e:
            print(f"⚠️ Scoring failed for {candidate.name}: {e}")
            score = None

        profiles.append({
            "name": result.get("title", "Unknown"),
            "linkedin_url": result.get("link", ""),
            "current_title": result.get("snippet", ""),
            "location": "",
            "summary": result.get("snippet", ""),
            "experience": [],
            "education": [],
            "skills": detected_skills,
            "score": score.overall_score if score else 0,
            "matched_skills": score.matched_skills if score else [],
            "missing_skills": score.missing_skills if score else [],
        })

    return profiles