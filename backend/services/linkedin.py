from config.settings import settings
import requests

from backend.services.scorer import score_candidate
from backend.models.schemas import Candidate, JobDescription
from backend.services.firestore_db import get_job_description


def scrape_linkedin_profiles(search_keywords: str, jd_id: str, max_profiles: int = 5):

    print("🔍 Searching via SerpAPI:", search_keywords)
    print("🔑 SERP KEY:", settings.serp_api_key)

    query = f'site:linkedin.com/in "{search_keywords}" -jobs -hiring'

    url = "https://serpapi.com/search"

    params = {
        "q": query,
        "api_key": settings.serp_api_key,
        "num": max_profiles
    }

    response = requests.get(url, params=params)
    data = response.json()

    profiles = []

    # ✅ NEW
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
        print("👉 Result:", result)

        text = result.get("snippet", "").lower()

        # ✅ simple skill detection
        detected_skills = []
        for skill in ["python", "java", "sql", "react", "aws"]:
            if skill in text:
                detected_skills.append(skill)

        candidate = Candidate(
            candidate_id="linkedin_" + result.get("link", ""),
            jd_id=jd_id,
            name=result.get("title", "Unknown"),
            email="",
            phone="",
            linkedin_url=result.get("link", ""),
            current_title=result.get("snippet", ""),
            years_experience=0,
            skills=detected_skills,
            education="",
            resume_text=text,
            status="Sourced",
            source="LinkedIn",
        )

        score = score_candidate(candidate, jd)

        profiles.append({
            "name": result.get("title", "Unknown"),
            "linkedin_url": result.get("link", ""),
            "current_title": result.get("snippet", ""),
            "location": "",
            "summary": result.get("snippet", ""),
            "experience": [],
            "education": [],
            "skills": detected_skills,

            # ✅ NEW FIELDS (no structure break)
            "score": score.overall_score,
            "matched_skills": score.matched_skills,
            "missing_skills": score.missing_skills,
        })

    return profiles