"""
Records API endpoints for managing educational records
"""

from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import List

router = APIRouter()
from fastapi import Depends, HTTPException, status
from typing import Optional
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.record import Record
from pydantic import BaseModel


class RecordResponse(BaseModel):
    id: int
    educator_id: int
    title: str
    description: Optional[str] = None
    record_type: Optional[str] = None
    status: Optional[str] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    created_at: Optional[str] = None


@router.get("/", response_model=List[RecordResponse])
async def list_records(
    skip: int = 0,
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    """List educator's records with pagination.

    Returns a list of record summaries for the current authenticated educator.
    """
    try:
        query = db.query(Record).filter(Record.educator_id == current_educator.id)
        records = query.order_by(Record.created_at.desc()).offset(skip).limit(limit).all()

        result = []
        for r in records:
            result.append({
                "id": r.id,
                "educator_id": r.educator_id,
                "title": r.title,
                "description": r.description,
                "record_type": r.record_type.value if r.record_type else None,
                "status": r.status.value if r.status else None,
                "student_id": r.student_id,
                "student_name": r.student_name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/")
async def create_record_placeholder():
    """Create new educational record (placeholder)"""
    return {"message": "Create record endpoint - implementation in progress"}