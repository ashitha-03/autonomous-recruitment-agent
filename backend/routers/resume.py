"""
backend/routers/resume.py
Resume upload using Agentic approach.
Gemini agent autonomously orchestrates the evaluation pipeline.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from backend.services.recruitment_agent import evaluate_resume_agent
from backend.services.firestore_db import get_job_description

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload")
async def upload_resume(
    files: List[UploadFile] = File(...),
    jd_id: str = Form(...),
):
    """
    Upload resumes — Gemini agent autonomously evaluates each one.
    Pipeline: Agent → parse → duplicate check → score → explain → save
    """
    allowed = (".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".tiff")
    for f in files:
        if not f.filename.lower().endswith(allowed):
            raise HTTPException(
                status_code=400,
                detail=f"{f.filename} — unsupported type."
            )

    # Verify JD exists
    jd_data = get_job_description(jd_id)
    if not jd_data:
        raise HTTPException(status_code=404, detail="Job Description not found")

    results = []
    errors = []

    for file in files:
        try:
            file_bytes = await file.read()
            # Agent handles everything autonomously
            result = evaluate_resume_agent(file_bytes, file.filename, jd_id)
            results.append(result)
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    return {
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "message": f"Agent processed {len(results)} resume(s)",
    }