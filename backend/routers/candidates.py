"""
backend/routers/candidates.py
Candidate endpoints - now using Firestore
"""
from fastapi import APIRouter, HTTPException
from backend.services.firestore_db import list_candidates, update_candidate_status

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("/")
async def get_candidates(jd_id: str = None):
    try:
        return list_candidates(jd_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{candidate_id}/status")
async def update_status(candidate_id: str, status: str):
    try:
        update_candidate_status(candidate_id, status)
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str):
    try:
        from backend.services.firestore_db import _get_db
        db = _get_db()
        db.collection("candidates").document(candidate_id).delete()
        return {"message": "Candidate deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))