# backend/services/recruitment_agent.py
"""
Agentic Recruitment Pipeline
=============================
Parsing:     Google Cloud Document AI (OCR) → pdfplumber fallback
Duplicate:   O(1) Firebase hash lookup
Scoring:     Deterministic algorithm (50% skills, 35% exp, 15% edu)
Explanation: OpenRouter Llama 3 (AI-generated professional assessment)
Storage:     Firebase Firestore
"""
import hashlib
from backend.models.schemas import Candidate, JobDescription
from backend.services.scorer import score_candidate
from backend.services.firestore_db import save_candidate, get_job_description
from config.settings import settings

_context = {}



def is_valid_resume(text: str) -> bool:
    keywords = [
        "experience", "education", "skills",
        "projects", "internship", "work experience",
        "technical skills", "summary"
    ]
    text_lower = text.lower()
    return sum(1 for k in keywords if k in text_lower) >= 2


# ── TOOL 1: PARSE RESUME ──────────────────────────────────────────────────────
def parse_resume_tool(filename: str) -> dict:
    """
    Parses resume using Google Cloud Document AI OCR.
    Auto-creates processor if not exists.
    Falls back to pdfplumber if Document AI unavailable.
    """
    try:
        file_bytes = _context.get("file_bytes")
        if not file_bytes:
            return {"error": "No file available"}

        resume_text = None
        candidate_base = None
        parser_used = "unknown"

        # ── Try Document AI first ──────────────────────────────────────────────
        try:
            from backend.services.document_ai_parser import parse_resume_with_docai
            resume_text, candidate_base = parse_resume_with_docai(file_bytes, filename)
            parser_used = "Document AI"
            print(f"✅ Document AI parsed: {filename}")
        except Exception as docai_error:
            print(f"⚠️ Document AI failed: {docai_error}")
            print("🔄 Falling back to pdfplumber...")

            # ── Fallback to pdfplumber ─────────────────────────────────────────
            try:
                from backend.services.resume_parser import parse_resume as _parse
                resume_text, candidate_base = _parse(file_bytes, filename)
                parser_used = "pdfplumber"
                print(f"✅ pdfplumber parsed: {filename}")
            except Exception as pdf_error:
                print(f"❌ pdfplumber also failed: {pdf_error}")
                return {"error": f"All parsers failed: {str(pdf_error)}"}

         # ❌ If no text extracted
        if not resume_text or len(resume_text.strip()) < 20:
            return {
                "is_resume": False,
                "error": f"Could not extract text from '{filename}'"
            }

# ✅ Validate resume content
        if not is_valid_resume(resume_text):
            return {
                "is_resume": False,
                "error": f"'{filename}' is not a valid resume"
            }

        # ── Validate it's a resume ─────────────────────────────────────────────
        resume_keywords = [
            "experience", "education", "skills", "project", "internship",
            "university", "college", "degree", "bachelor", "master",
            "developer", "engineer", "analyst", "manager", "work"
        ]
        keyword_count = sum(1 for kw in resume_keywords if kw in resume_text.lower())

        if keyword_count < 3:
            return {
                "is_resume": False,
                "error": f"'{filename}' does not appear to be a resume (only {keyword_count} resume keywords found)"
            }

        _context["resume_text"] = resume_text
        _context["candidate_base"] = candidate_base
        _context["parser_used"] = parser_used

        return {
            "is_resume": True,
            "parser_used": parser_used,
            "name": candidate_base.name,
            "email": candidate_base.email,
            "phone": str(candidate_base.phone or ""),
            "years_experience": float(candidate_base.years_experience or 0),
            "skills": candidate_base.skills[:10],
            "education": candidate_base.education or "",
        }

    except Exception as e:
        return {"error": str(e)}


# ── TOOL 2: DUPLICATE CHECK ───────────────────────────────────────────────────
def check_duplicate_tool(email: str, jd_id: str) -> dict:
    """
    O(1) duplicate check using email+jd_id hash as Firestore document ID.
    No scanning needed — instant single-document lookup.
    """
    try:
        doc_id = hashlib.md5(f"{email}_{jd_id}".encode()).hexdigest()
        from backend.services.firestore_db import _get_db
        db = _get_db()
        doc = db.collection("candidates").document(doc_id).get()
        if doc.exists:
            return {"is_duplicate": True, "message": "Candidate already applied for this JD"}
        return {"is_duplicate": False, "message": "New candidate — proceed with evaluation"}
    except Exception as e:
        return {"error": str(e), "is_duplicate": False}


# ── TOOL 3: SCORE CANDIDATE ───────────────────────────────────────────────────
def score_candidate_tool(jd_id: str, email: str) -> dict:
    """
    Deterministic scoring algorithm.
    Same resume + same JD = ALWAYS same score (no randomness).

    Weights:
    - Skills Match:     50%
    - Experience Match: 35%
    - Education Match:  15%

    Thresholds:
    - >= 70 → Shortlist
    - >= 50 → Maybe
    - <  50 → Reject
    """
    try:
        candidate_base = _context.get("candidate_base")
        resume_text = _context.get("resume_text", "")

        if not candidate_base:
            return {"error": "No candidate data — run parse_resume_tool first"}

        jd_data = get_job_description(jd_id)
        if not jd_data:
            return {"error": f"Job Description '{jd_id}' not found"}

        # Build JD object
        jd = JobDescription(
            jd_id=jd_data["jd_id"],
            role_title=jd_data["role_title"],
            department=jd_data.get("department", ""),
            summary=jd_data.get("summary", ""),
            responsibilities=(jd_data.get("responsibilities") or "").split(" | "),
            required_skills=[
                s.strip() for s in
                (jd_data.get("required_skills") or "").replace(",", ", ").split(", ")
                if s.strip()
            ],
            preferred_skills=[
                s.strip() for s in
                (jd_data.get("preferred_skills") or "").replace(",", ", ").split(", ")
                if s.strip()
            ],
            experience_years=int(jd_data.get("experience_years") or 0),
            work_mode=jd_data.get("work_mode", ""),
        )

        # Use email+jd_id hash as document ID (enables O(1) duplicate check)
        doc_id = hashlib.md5(f"{email}_{jd_id}".encode()).hexdigest()

        candidate = Candidate(
            candidate_id=doc_id,
            jd_id=jd_id,
            name=candidate_base.name,
            email=candidate_base.email,
            phone=candidate_base.phone,
            linkedin_url=candidate_base.linkedin_url,
            current_title=None,
            years_experience=candidate_base.years_experience,
            skills=candidate_base.skills,
            education=candidate_base.education,
            resume_text=resume_text,
            status="Applied",
            source="Resume Upload",
        )

        # Deterministic scoring
        score = score_candidate(candidate, jd)
        score.candidate_id = doc_id

        _context["candidate"] = candidate
        _context["score"] = score
        _context["jd_data"] = jd_data

        return {
            "overall_score": score.overall_score,
            "skills_match": score.skills_match,
            "experience_match": score.experience_match,
            "education_match": score.education_match,
            "matched_skills": score.matched_skills,
            "missing_skills": score.missing_skills,
            "recommendation": score.recommendation,
        }

    except Exception as e:
        return {"error": str(e)}


# ── TOOL 4: GENERATE AI EXPLANATION ──────────────────────────────────────────
def generate_explanation_tool() -> str:
    """
    Generates professional AI explanation.
    Primary:  Vertex AI Gemini
    Fallback: OpenRouter Llama 3
    Last:     Template text
    """
    candidate = _context.get("candidate")
    score = _context.get("score")
    jd_data = _context.get("jd_data", {})

    if not candidate or not score:
        return "Candidate evaluated and processed."

    matched = ", ".join(score.matched_skills) if score.matched_skills else "None"
    missing = ", ".join(score.missing_skills) if score.missing_skills else "None"
    matched_count = len(score.matched_skills) if score.matched_skills else 0
    total_required = matched_count + (len(score.missing_skills) if score.missing_skills else 0)

    prompt = f"""You are a professional HR recruiter. Write a concise 2-3 sentence assessment.

Candidate: {candidate.name}
Role: {jd_data.get('role_title', 'the position')} at {jd_data.get('company_name', 'our company')}
Overall Score: {score.overall_score}/100
Skills Match: {score.skills_match}%
Experience Match: {score.experience_match}%
Education Match: {score.education_match}%
Matched Skills: {matched}
Missing Skills: {missing}
Recommendation: {score.recommendation}

Write a professional explanation of why this candidate was {'shortlisted' if score.recommendation == 'Shortlist' else 'not selected'}. Be specific about skills."""

    # ── Try Vertex AI Gemini first ─────────────────────────────────────────────
    try:
        import google.generativeai as genai
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project_id,
            location=settings.vertex_ai_location,
        )
        response = client.models.generate_content(
            model=settings.vertex_ai_model,
            contents=prompt,
        )
        explanation = response.text.strip()
        print(f"✅ Vertex AI explanation generated for {candidate.name}")
        return explanation
    except Exception as e:
        print(f"⚠️ Vertex AI failed: {str(e)[:60]} — trying OpenRouter...")

    # ── Fallback: OpenRouter Llama 3 ──────────────────────────────────────────
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        explanation = response.choices[0].message.content.strip()
        print(f"✅ OpenRouter explanation generated for {candidate.name}")
        return explanation
    except Exception as e:
        print(f"⚠️ OpenRouter failed: {e} — using template")

    # ── Last resort: Template ──────────────────────────────────────────────────
    return (
        f"{candidate.name} achieved a match score of {score.overall_score}/100 for the "
        f"{jd_data.get('role_title', 'position')} role. "
        f"The candidate matched {matched_count} out of {total_required} required skills "
        f"with {score.experience_match:.0f}% experience alignment. "
        f"Recommendation: {score.recommendation}."
    )


# ── TOOL 5: SAVE TO DATABASE ──────────────────────────────────────────────────
def save_to_database_tool(explanation: str) -> dict:
    """Saves candidate with AI explanation to Firestore."""
    try:
        candidate = _context.get("candidate")
        score = _context.get("score")

        if not candidate or not score:
            return {"error": "No candidate data to save"}

        score.rejection_reason = explanation

        # Auto-determine status based on score
        if score.overall_score >= 70:
            candidate.status = "Shortlisted"
        elif score.overall_score >= 50:
            candidate.status = "Maybe"
        else:
            candidate.status = "Rejected"

        save_candidate(candidate, score)
        print(f"✅ Saved to Firestore: {candidate.name} ({candidate.status})")

        return {
            "success": True,
            "candidate_id": candidate.candidate_id,
            "name": candidate.name,
            "status": candidate.status,
            "score": score.overall_score,
        }

    except Exception as e:
        return {"error": str(e)}


# ── MAIN PIPELINE ─────────────────────────────────────────────────────────────
def _run_pipeline(filename: str, jd_id: str) -> dict:
    """
    Autonomous recruitment evaluation pipeline.

    Step 1: Parse resume (Document AI → pdfplumber fallback)
    Step 2: Check duplicate (O(1) hash lookup)
    Step 3: Score candidate (deterministic algorithm)
    Step 4: Generate AI explanation (OpenRouter)
    Step 5: Save to Firestore
    Step 6: Return result to frontend
    """
    print(f"\n{'='*50}")
    print(f"🤖 Evaluating: {filename}")
    print(f"{'='*50}")

    # ── Step 1: Parse ──────────────────────────────────────────────────────────
    print("📄 Step 1: Parsing resume...")
    parse_result = parse_resume_tool(filename)

    if parse_result.get("error") and not parse_result.get("is_resume", True):
        print(f"❌ Not a resume: {parse_result.get('error')}")
        return {
            "filename": filename,
            "candidate_id": None,
            "name": filename,
            "email": "—",
            "status": "Rejected",
            "score": None,
            "recommendation": "Not a Resume",
            "rejection_reason": parse_result.get("error", "Not a valid resume"),
            "matched_skills": [],
            "missing_skills": [],
        }

    if parse_result.get("error"):
        print(f"❌ Parse error: {parse_result['error']}")
        return {
            "filename": filename,
            "candidate_id": None,
            "name": filename,
            "email": "—",
            "status": "Error",
            "score": None,
            "recommendation": None,
            "rejection_reason": parse_result["error"],
            "matched_skills": [],
            "missing_skills": [],
        }

    email = parse_result.get("email", "unknown@email.com")
    name = parse_result.get("name", filename)
    parser_used = parse_result.get("parser_used", "unknown")
    print(f"✅ Parsed: {name} ({email}) via {parser_used}")

    

    # ── Step 2: Duplicate Check ────────────────────────────────────────────────
    print("🔍 Step 2: Checking duplicate...")
    dup_result = check_duplicate_tool(email, jd_id)

    if dup_result.get("is_duplicate"):
        print(f"⚠️ Duplicate found: {name}")
        return {
            "filename": filename,
            "candidate_id": None,
            "name": name,
            "email": email,
            "status": "Duplicate",
            "score": None,
            "recommendation": "Already Applied",
            "rejection_reason": "This candidate has already applied for this position.",
            "matched_skills": [],
            "missing_skills": [],
        }
    print("✅ New candidate — proceeding")

    # ── Step 3: Score ──────────────────────────────────────────────────────────
    print("📊 Step 3: Scoring candidate...")
    score_result = score_candidate_tool(jd_id, email)

    if isinstance(score_result, dict) and score_result.get("error"):
        print(f"❌ Scoring error: {score_result['error']}")
        return {
            "filename": filename,
            "candidate_id": None,
            "name": name,
            "email": email,
            "status": "Error",
            "score": None,
            "recommendation": None,
            "rejection_reason": f"Scoring failed: {score_result['error']}",
            "matched_skills": [],
            "missing_skills": [],
        }

    candidate = _context.get("candidate")
    score = _context.get("score")

    if not candidate or not score:
        return {
            "filename": filename,
            "candidate_id": None,
            "name": name,
            "email": email,
            "status": "Error",
            "score": None,
            "recommendation": None,
            "rejection_reason": "Internal scoring error",
            "matched_skills": [],
            "missing_skills": [],
        }

    print(f"✅ Score: {score.overall_score}/100 → {score.recommendation}")

    # ── Step 4: AI Explanation ─────────────────────────────────────────────────
    print("💡 Step 4: Generating AI explanation...")
    explanation = generate_explanation_tool()
    print(f"✅ Explanation: {explanation[:60]}...")

    # ── Step 5: Save ───────────────────────────────────────────────────────────
    print("💾 Step 5: Saving to Firebase...")
    save_result = save_to_database_tool(explanation)

    if save_result.get("error"):
        print(f"❌ Save error: {save_result['error']}")

    print(f"✅ Done: {candidate.name} → {candidate.status}")
    print(f"{'='*50}\n")

    # ── Step 6: Return ─────────────────────────────────────────────────────────
    return {
        "filename": filename,
        "candidate_id": candidate.candidate_id,
        "name": candidate.name,
        "email": candidate.email,
        "status": candidate.status,
        "score": score.overall_score,
        "recommendation": score.recommendation,
        "rejection_reason": explanation,
        "matched_skills": score.matched_skills or [],
        "missing_skills": score.missing_skills or [],
    }


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def evaluate_resume_agent(file_bytes: bytes, filename: str, jd_id: str) -> dict:
    """
    Main entry point called by resume router.
    Runs the full autonomous evaluation pipeline.
    """
    global _context
    _context = {"file_bytes": file_bytes, "jd_id": jd_id}

    try:
        return _run_pipeline(filename, jd_id)
    except Exception as e:
        print(f"❌ Pipeline crashed: {e}")
        return {
            "filename": filename,
            "candidate_id": None,
            "name": filename,
            "email": "—",
            "status": "Error",
            "score": None,
            "recommendation": None,
            "rejection_reason": str(e),
            "matched_skills": [],
            "missing_skills": [],
        }
    finally:
        _context = {}