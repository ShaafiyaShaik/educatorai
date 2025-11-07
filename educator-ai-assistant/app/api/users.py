"""
User management and search API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class UserSearchResponse(BaseModel):
    id: int
    email: str
    full_name: str
    department: Optional[str]
    available: bool = True
    
    class Config:
        from_attributes = True

@router.get("/search", response_model=List[UserSearchResponse])
async def search_users(
    q: str,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Search for users by email or name"""
    if len(q.strip()) < 2:
        return []
    
    query = db.query(Educator).filter(
        or_(
            Educator.email.ilike(f"%{q}%"),
            Educator.full_name.ilike(f"%{q}%")
        ),
        Educator.id != current_educator.id  # Exclude current user
    ).limit(10)
    
    users = query.all()
    
    # Convert to response format
    result = []
    for user in users:
        result.append(UserSearchResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            available=True  # In real system, check calendar availability
        ))
    
    return result

@router.get("/availability/{user_id}")
async def check_user_availability(
    user_id: int,
    start_time: str,
    end_time: str,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Check if a user is available for a specific time slot"""
    user = db.query(Educator).filter(Educator.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # In a real system, check user's calendar for conflicts
    # For now, return mock availability
    return {
        "user_id": user_id,
        "available": True,
        "conflicts": []
    }