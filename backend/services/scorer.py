"""
backend/services/scorer.py


"""
from datetime import datetime
from backend.models.schemas import Candidate, JobDescription, CandidateScore


# ── Education scoring map ──────────────────────────────────────────────────────
EDUCATION_SCORES = {
    "phd": 100, "ph.d": 100, "doctorate": 100,
    "master": 90, "msc": 90, "mba": 90, "m.tech": 90, "mca": 90, "me": 90,
    "bachelor": 75, "bsc": 75, "b.tech": 75, "be": 75, "bca": 75, "b.e": 75,
    "diploma": 60, "certificate": 50,
}

def _normalize_skill(skill: str) -> str:
    """
    Cleans AI-generated long skill sentences into core keywords
    WITHOUT changing scoring logic
    """
    skill = skill.lower()

    # Remove common AI filler words
    noise_words = [
        "solid foundation in",
        "understanding of",
        "basic knowledge of",
        "strong knowledge of",
        "good knowledge of",
        "experience with",
        "proficiency in",
        "programming language",
        "and its core libraries",
    ]

    for word in noise_words:
        skill = skill.replace(word, "")

    return skill.strip()


def _score_skills(candidate: Candidate, jd: JobDescription) -> tuple[float, list, list]:
    """
    SAME LOGIC — only better matching
    """

    required = [_normalize_skill(s) for s in (jd.required_skills or []) if s.strip()]
    preferred = [_normalize_skill(s) for s in (jd.preferred_skills or []) if s.strip()]

    candidate_skills = [s.lower().strip() for s in (candidate.skills or [])]
    resume_text = (candidate.resume_text or "").lower()

    matched_required = []
    missing_required = []
    matched_preferred = []

    for skill in required:
        if any(skill in cs or cs in skill for cs in candidate_skills) or skill in resume_text:
            matched_required.append(skill.title())
        else:
            missing_required.append(skill.title())

    for skill in preferred:
        if any(skill in cs or cs in skill for cs in candidate_skills) or skill in resume_text:
            matched_preferred.append(skill.title())

    # SAME scoring logic (UNCHANGED)
    if required:
        required_score = (len(matched_required) / len(required)) * 100
    else:
        required_score = 70.0

    if preferred:
        preferred_score = (len(matched_preferred) / len(preferred)) * 100
    else:
        preferred_score = 50.0

    skills_score = (required_score * 0.70) + (preferred_score * 0.30)

    return round(skills_score, 1), matched_required, missing_required

def _score_experience(candidate: Candidate, jd: JobDescription) -> float:
    """
    Scores experience match.
    """
    required_years = float(jd.experience_years or 0)
    candidate_years = float(candidate.years_experience or 0)

    if required_years == 0:
        return 80.0  # No requirement = good score

    if candidate_years >= required_years:
        # Has enough experience
        if candidate_years >= required_years * 1.5:
            return 100.0  # Overqualified but good
        return 85.0 + min(15.0, (candidate_years - required_years) * 3)
    else:
        # Less experience than required
        ratio = candidate_years / required_years
        return round(ratio * 70, 1)  # Max 70% if under-experienced


def _score_education(candidate: Candidate) -> float:
    """
    Scores education based on degree keywords.
    """
    education = (candidate.education or "").lower()
    resume_text = (candidate.resume_text or "").lower()
    combined = f"{education} {resume_text}"

    for keyword, score in EDUCATION_SCORES.items():
        if keyword in combined:
            return float(score)

    return 50.0  # Unknown education = neutral


def _get_recommendation(overall_score: float) -> str:
    if overall_score >= 60:
        return "Shortlist"
    elif overall_score >= 40:
        return "Maybe"
    else:
        return "Reject"


def score_candidate(candidate: Candidate, jd: JobDescription) -> CandidateScore:
    
    # Calculate each component
    skills_score, matched_skills, missing_skills = _score_skills(candidate, jd)
    experience_score = _score_experience(candidate, jd)
    education_score = _score_education(candidate)

    # Weighted overall score
    overall_score = round(
        (skills_score * 0.50) +
        (experience_score * 0.35) +
        (education_score * 0.15),
        1
    )

    recommendation = _get_recommendation(overall_score)

    print(f"📊 Score breakdown for {candidate.name}:")
    print(f"   Skills:     {skills_score}% (weight: 50%)")
    print(f"   Experience: {experience_score}% (weight: 35%)")
    print(f"   Education:  {education_score}% (weight: 15%)")
    print(f"   Overall:    {overall_score}% → {recommendation}")
    print(f"   Matched:    {matched_skills}")
    print(f"   Missing:    {missing_skills}")

    return CandidateScore(
        candidate_id=candidate.candidate_id or "",
        jd_id=jd.jd_id or "",
        overall_score=overall_score,
        skills_match=skills_score,
        experience_match=experience_score,
        education_match=education_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        ai_summary="",
        recommendation=recommendation,
        rejection_reason="",
        scored_at=datetime.utcnow(),
    )