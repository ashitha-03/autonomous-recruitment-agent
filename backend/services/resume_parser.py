"""
backend/services/resume_parser.py
Simple resume parser - NO OCR, NO Vertex AI needed.
Handles digital PDF and DOCX files only.
OCR for scanned/handwritten resumes → Week 2 feature.
"""
import io
import re
import pdfplumber
from docx import Document as DocxDocument
from backend.models.schemas import CandidateBase


KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "swift", "kotlin", "php", "scala", "matlab",
    "fastapi", "flask", "django", "react", "angular", "vue", "nodejs",
    "express", "spring", "laravel",
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
    "supabase", "firebase", "dynamodb",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "jenkins",
    "github", "gitlab", "linux",
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "pandas", "numpy", "nlp", "computer vision",
    "vertex ai", "openai", "langchain", "gemini",
    "rest api", "graphql", "microservices", "agile", "scrum", "git",
    "html", "css", "bootstrap", "tailwind", "figma",
    "excel", "powerpoint", "tableau", "power bi",
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs]).strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx") or lower.endswith(".doc"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Use PDF or DOCX.")


def extract_email(text: str) -> str:
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0).lower() if match else "unknown@email.com"


def extract_phone(text: str) -> str | None:
    match = re.search(r'(\+?\d[\d\s\-().]{8,15}\d)', text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    skip = ['@', 'http', 'www', 'linkedin', 'github', 'phone',
            'email', 'address', 'objective', 'summary',
            'experience', 'education', 'skills', 'curriculum', 'resume', 'cv',
            'candidate name', 'name:']
    for line in lines[:10]:
        if any(p in line.lower() for p in skip):
            continue
        if re.search(r'\d{4,}', line):
            continue
        # Remove any non-letter characters from start of line
        line = re.sub(r'^[^a-zA-Z]+', '', line).strip()
        if not line:
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and len(line) <= 50:
            if sum(1 for w in words if len(w) > 2) >= 2:
                return ' '.join(words)
    return lines[0] if lines else "Unknown Candidate"


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        if skill.lower() in text_lower:
            found.append(skill.title())
    return sorted(list(set(found)))


def extract_experience_years(text: str) -> float:
    matches = re.findall(r'(\d+)\+?\s*years?', text.lower())
    if matches:
        numbers = [int(m) for m in matches if 0 < int(m) < 40]
        if numbers:
            return float(max(numbers))
    job_count = len(re.findall(
        r'\b(engineer|developer|analyst|manager|intern|lead|architect|designer)\b',
        text.lower()
    ))
    return float(min(job_count, 10))


def extract_education(text: str) -> str | None:
    degrees = ["phd", "ph.d", "doctorate", "master", "msc", "mba",
               "m.tech", "me ", "bachelor", "bsc", "b.tech", "be ",
               "bca", "b.e", "diploma", "certificate"]
    for line in text.split('\n'):
        if any(d in line.lower() for d in degrees):
            clean = line.strip()
            if 5 < len(clean) < 150:
                return clean
    return None


def extract_linkedin(text: str) -> str | None:
    match = re.search(r'linkedin\.com/in/[\w\-]+', text.lower())
    return f"https://{match.group(0)}" if match else None
def is_resume(text: str) -> bool:
    text = text.lower()

    keywords = [
        "education", "skills", "experience",
        "projects", "internship", "summary"
    ]

    count = 0
    for word in keywords:
        if word in text:
            count += 1

    return count >= 3

def parse_resume(file_bytes: bytes, filename: str) -> tuple[str, CandidateBase | None]:
    resume_text = extract_text(file_bytes, filename)

    # 🚨 ADD THIS VALIDATION
    if not is_resume(resume_text):
        return resume_text, None  # reject non-resume

    candidate = CandidateBase(
        name=extract_name(resume_text),
        email=extract_email(resume_text),
        phone=extract_phone(resume_text),
        linkedin_url=extract_linkedin(resume_text),
        current_title=None,
        years_experience=extract_experience_years(resume_text),
        skills=extract_skills(resume_text),
        education=extract_education(resume_text),
        resume_text=resume_text,
    )

    return resume_text, candidate