"""
backend/routers/jd.py
Job Description API endpoints - Firestore + PDF export
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from backend.models.schemas import JDGenerateRequest, JobDescription
from backend.services.jd_generator import generate_job_description
from backend.services.firestore_db import (
    save_job_description, list_job_descriptions,
    get_job_description, delete_job_description, update_job_description
)
from backend.services.pdf_generator import generate_jd_pdf
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/jd", tags=["Job Descriptions"])


class UpdateJDRequest(BaseModel):
    role_title: Optional[str] = None
    department: Optional[str] = None
    summary: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    preferred_skills: Optional[str] = None
    experience_years: Optional[int] = None
    work_mode: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    company_name: Optional[str] = None


@router.post("/generate", response_model=JobDescription)
async def generate_jd(req: JDGenerateRequest):
    try:
        jd = generate_job_description(req)
        save_job_description(jd)
        return jd
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_jds():
    try:
        return list_job_descriptions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{jd_id}")
async def get_jd(jd_id: str):
    jd = get_job_description(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job Description not found")
    return jd


@router.delete("/{jd_id}")
async def delete_jd(jd_id: str):
    try:
        delete_job_description(jd_id)
        return {"message": "Job Description deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{jd_id}")
async def update_jd(jd_id: str, req: UpdateJDRequest):
    try:
        data = {k: v for k, v in req.dict().items() if v is not None}
        update_job_description(jd_id, data)
        return {"message": "Job Description updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{jd_id}/pdf")
async def download_jd_pdf(jd_id: str):
    """Download JD as professional PDF."""
    try:
        jd = get_job_description(jd_id)
        if not jd:
            raise HTTPException(status_code=404, detail="Job Description not found")

        pdf_bytes = generate_jd_pdf(jd)
        filename = f"{jd.get('role_title', 'JD').replace(' ', '_')}_JD.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))