"""
Records API endpoints for managing educational records
"""

from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import List

router = APIRouter()

@router.get("/")
async def list_records():
    """List educational records"""
    # For now, return empty list until we implement full record tracking
    return []

@router.post("/")
async def create_record():
    """Create new educational record"""
    return {"message": "Create record endpoint - implementation in progress"}