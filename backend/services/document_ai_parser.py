

import io
import re
from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from backend.models.schemas import CandidateBase
from config.settings import settings
import json
from google.oauth2 import service_account

# Document AI location — must be 'us' or 'eu'
DOCAI_LOCATION = "us"
PROCESSOR_TYPE = "OCR_PROCESSOR"
PROCESSOR_DISPLAY_NAME = "recruitai-resume-ocr"


# ── Known Skills List ──────────────────────────────────────────────────────────
KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "swift", "kotlin", "php", "scala", "matlab",
    "fastapi", "flask", "django", "react", "angular", "vue", "nodejs",
    "express", "spring", "laravel",
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
    "supabase", "firebase", "firestore", "dynamodb",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "jenkins",
    "github", "gitlab", "linux",
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "pandas", "numpy", "nlp", "computer vision",
    "vertex ai", "openai", "langchain", "gemini", "document ai",
    "rest api", "graphql", "microservices", "agile", "scrum", "git",
    "html", "css", "bootstrap", "tailwind", "figma",
    "excel", "powerpoint", "tableau", "power bi",
]

def _get_docai_client():
    """Returns Document AI client with credentials (Render-safe)."""
    
    opts = ClientOptions(
        api_endpoint=f"{DOCAI_LOCATION}-documentai.googleapis.com"
    )

    print("ENV LOADED:", bool(settings.google_credentials_json))

    if settings.google_credentials_json:
        try:
            creds_dict = json.loads(settings.google_credentials_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)

            print("✅ USING ENV DOC AI")

            return documentai.DocumentProcessorServiceClient(
                credentials=credentials,
                client_options=opts
            )
        except Exception as e:
            print("❌ JSON ERROR:", e)

    print("⚠️ FALLBACK DOC AI")
    return documentai.DocumentProcessorServiceClient(client_options=opts)
def _get_or_create_processor() -> str:
    # Check .env first
    if settings.document_ai_processor_id:
        print(f"✅ Using processor: {settings.document_ai_processor_id}")
        return settings.document_ai_processor_id

    # Check Firestore
    try:
        from backend.services.firestore_db import _get_db
        db = _get_db()
        config_doc = db.collection("system_config").document("document_ai").get()
        if config_doc.exists:
            processor_id = config_doc.to_dict().get("processor_id")
            if processor_id:
                print(f"✅ Using processor from Firestore: {processor_id}")
                return processor_id
    except Exception as e:
        print(f"⚠️ Firestore check failed: {e}")

    raise Exception("No processor ID found! Add DOCUMENT_AI_PROCESSOR_ID to .env")

    # Create new processor
    print("🔧 Creating new Document AI OCR processor...")
    client = _get_docai_client()
    parent = client.common_location_path(settings.google_cloud_project_id, DOCAI_LOCATION)

    processor = client.create_processor(
        parent=parent,
        processor=documentai.Processor(
            type_=PROCESSOR_TYPE,
            display_name=PROCESSOR_DISPLAY_NAME,
        ),
    )

    processor_id = processor.name.split("/")[-1]
    print(f"✅ Created processor: {processor_id}")

    # Save to Firestore for future use
    try:
        from backend.services.firestore_db import _get_db
        db = _get_db()
        db.collection("system_config").document("document_ai").set({
            "processor_id": processor_id,
            "processor_name": processor.name,
            "created_at": processor.create_time.isoformat() if processor.create_time else "",
        })
        print(f"✅ Saved processor ID to Firestore")
    except Exception as e:
        print(f"⚠️ Could not save processor ID: {e}")

    return processor_id


def extract_text_with_document_ai(file_bytes: bytes, mime_type: str = "application/pdf") -> str:
    """
    Extracts text from document using Document AI OCR.
    Handles digital PDFs, scanned PDFs, and images.
    """
    processor_id = _get_or_create_processor()

    client = _get_docai_client()
    name = client.processor_path(
        settings.google_cloud_project_id,
        DOCAI_LOCATION,
        processor_id
    )

    raw_document = documentai.RawDocument(
        content=file_bytes,
        mime_type=mime_type,
    )

    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
    )

    result = client.process_document(request=request)
    return result.document.text


def _get_mime_type(filename: str) -> str:
    """Returns MIME type based on file extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    elif lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif lower.endswith(".png"):
        return "image/png"
    elif lower.endswith(".tiff"):
        return "image/tiff"
    else:
        return "application/pdf"


# ── Info Extraction ────────────────────────────────────────────────────────────

def extract_email(text: str) -> str:
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0).lower() if match else "unknown@email.com"


def extract_phone(text: str) -> str | None:
    match = re.search(r'(\+?\d[\d\s\-().]{8,15}\d)', text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str:
    """Extract name from resume — improved for Document AI output."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    skip = ['@', 'http', 'www', 'linkedin', 'github', 'phone',
            'email', 'address', 'objective', 'summary', 'curriculum',
            'experience', 'education', 'skills', 'resume', 'cv', 'name:']

    for line in lines[:10]:
        if any(p in line.lower() for p in skip):
            continue
        if re.search(r'\d{4,}', line):
            continue
        
        line = re.sub(r'^[^a-zA-Z]+', '', line).strip()
        if not line:
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and len(line) <= 50:
            # Must have at least 2 words longer than 2 chars
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
               "bca", "b.e", "diploma", "mca", "bca", "certificate"]
    for line in text.split('\n'):
        if any(d in line.lower() for d in degrees):
            clean = line.strip()
            if 5 < len(clean) < 150:
                return clean
    return None


def extract_linkedin(text: str) -> str | None:
    match = re.search(r'linkedin\.com/in/[\w\-]+', text.lower())
    return f"https://{match.group(0)}" if match else None


# ── Main Parse Function ────────────────────────────────────────────────────────

def parse_resume_with_docai(file_bytes: bytes, filename: str) -> tuple[str, CandidateBase]:
   
    # Determine MIME type
    mime_type = _get_mime_type(filename)

   
    if filename.lower().endswith((".docx", ".doc")):
        from docx import Document as DocxDoc
        doc = DocxDoc(io.BytesIO(file_bytes))
        resume_text = "\n".join([p.text for p in doc.paragraphs]).strip()
    else:
        # Use Document AI for PDF and images
        print(f"🔍 Processing '{filename}' with Document AI...")
        resume_text = extract_text_with_document_ai(file_bytes, mime_type)

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