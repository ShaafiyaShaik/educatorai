"""
Alias routes to match frontend expectations for sections endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.api.students import get_filtered_section_students

router = APIRouter()

@router.get("/sections/{section_id}/students/filtered")
async def alias_filtered_students(
    section_id: int,
    pass_status: str | None = None,
    subject_filter: str | None = None,
    search: str | None = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db),
):
    # Proxy to the canonical students endpoint
    return await get_filtered_section_students(
        section_id=section_id,
        pass_status=pass_status,
        subject_filter=subject_filter,
        search=search,
        current_educator=current_educator,
        db=db,
    )
