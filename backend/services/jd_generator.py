"""
backend/services/jd_generator.py
Robust JD generation using Vertex AI (with retry + OpenRouter fallback)
"""
import json
import uuid
import time
from datetime import datetime
import google.generativeai as genai
from backend.models.schemas import JDGenerateRequest, JobDescription
from config.settings import settings


PROMPT_TEMPLATE = """
Generate a professional Job Description in JSON format.

Role: {role_title}
Department: {department}
Experience: {experience_years} years
Work Mode: {work_mode}
Location: {location}
Employment Type: {employment_type}
Salary Range: {salary_range}
Company: {company_name}
Skills Hints: {skills_hint}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "role_title": "{role_title}",
  "department": "{department}",
  "summary": "3-4 sentence compelling overview mentioning the company and role",
  "responsibilities": ["responsibility 1", "responsibility 2", "responsibility 3", "responsibility 4", "responsibility 5"],
  "required_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "preferred_skills": ["skill1", "skill2", "skill3"],
  "experience_years": {experience_years},
  "work_mode": "{work_mode}",
  "location": "{location}",
  "employment_type": "{employment_type}",
  "salary_range": "{salary_range}"
}}
"""


def _parse_raw(raw: str) -> dict | None:
    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end > start:
            raw = raw[start:end]
        return json.loads(raw.strip())
    except Exception:
        return None


def _try_vertex_ai(prompt: str) -> str | None:
    try:
        print("🔹 Using Vertex AI Gemini")

        import vertexai
        from vertexai.generative_models import GenerativeModel
        import os

        vertexai.init(
            project=settings.google_cloud_project_id,
            location="us-central1"
        )

        model = GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(prompt)

        return response.text.strip()

    except Exception as e:
        print(f"⚠️ Vertex AI error: {str(e)[:80]}")
        return None


def _try_openrouter(prompt: str) -> str | None:
    try:
        from openai import OpenAI
        print("🔄 Falling back to OpenRouter...")
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
        )
        print("✅ OpenRouter response received")
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ OpenRouter error: {e}")
        return None


def generate_job_description(req: JDGenerateRequest) -> JobDescription:

    prompt = PROMPT_TEMPLATE.format(
        role_title=req.role_title,
        department=req.department,
        experience_years=req.experience_years,
        work_mode=req.work_mode,
        location=req.location or "Not specified",
        employment_type=req.employment_type or "Full-time",
        salary_range=req.salary_range or "Competitive",
        company_name=settings.company_name,
        skills_hint=req.skills_hint or "Not specified",
    )

    # Vertex
    raw = _try_vertex_ai(prompt)

    # Fallback
    if not raw:
        raw = _try_openrouter(prompt)

    # Parse
    data = None
    if raw:
        data = _parse_raw(raw)
        if not data:
            print("⚠️ JSON parsing failed")

    # Template fallback
    if not data:
        print("🚨 Using template fallback JD")
        data = {
            "role_title": req.role_title,
            "department": req.department,
            "summary": f"{settings.company_name} is looking for a talented {req.role_title} to join our {req.department} team.",
            "responsibilities": [
                f"Design and develop solutions as a {req.role_title}",
                "Collaborate with cross-functional teams",
                "Write clean code",
                "Participate in reviews",
                "Debug and optimize systems",
            ],
            "required_skills": req.skills_hint.split(", ") if req.skills_hint else ["Problem Solving", "Communication"],
            "preferred_skills": ["Docker", "Cloud"],
            "experience_years": req.experience_years,
            "work_mode": req.work_mode,
            "location": req.location or "",
            "employment_type": req.employment_type or "Full-time",
            "salary_range": req.salary_range or "Competitive",
        }

    # ✅ NORMALIZATION (NO LOGIC CHANGE)
    def _normalize_skill(skill: str) -> str:
        skill = skill.lower()

        if "python" in skill:
            return "python"
        if "java" in skill:
            return "java"
        if "react" in skill:
            return "react"
        if "node" in skill:
            return "node"
        if "mongodb" in skill:
            return "mongodb"
        if "data structure" in skill:
            return "data structures"
        if "algorithm" in skill:
            return "algorithms"

        return skill.strip()

    if "required_skills" in data:
        data["required_skills"] = list({_normalize_skill(s) for s in data["required_skills"]})

    if "preferred_skills" in data:
        data["preferred_skills"] = list({_normalize_skill(s) for s in data["preferred_skills"]})

    # Final object
    jd = JobDescription(
        jd_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        company_name=settings.company_name,
        **data
    )

    return jd