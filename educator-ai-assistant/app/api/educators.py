"""
Educator API endpoints for managing educator profiles and authentication
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.auth import create_access_token, verify_password, get_password_hash, verify_token
from app.models.educator import Educator
import json

router = APIRouter()

# Pydantic models for request/response
class EducatorCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    office_location: Optional[str] = None
    phone: Optional[str] = None
    password: str

class EducatorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    office_location: Optional[str] = None
    phone: Optional[str] = None
    notification_preferences: Optional[dict] = None
    timezone: Optional[str] = None

class EducatorResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    employee_id: Optional[str]
    department: Optional[str]
    title: Optional[str]
    office_location: Optional[str]
    phone: Optional[str]
    is_active: bool
    timezone: str
    created_at: Optional[str]
    last_login: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str

def get_current_educator(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current authenticated educator"""
    educator = db.query(Educator).filter(Educator.email == token).first()
    if not educator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Educator not found"
        )
    return educator

@router.post("/register", response_model=EducatorResponse)
async def register_educator(educator_data: EducatorCreate, db: Session = Depends(get_db)):
    """Register a new educator"""
    # Check if educator already exists
    if db.query(Educator).filter(Educator.email == educator_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Handle empty employee_id - convert to None to avoid unique constraint issues
    employee_id = educator_data.employee_id if educator_data.employee_id and educator_data.employee_id.strip() else None
    
    # Check if employee_id already exists (if provided)
    if employee_id and db.query(Educator).filter(Educator.employee_id == employee_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already registered"
        )
    
    # Create new educator
    hashed_password = get_password_hash(educator_data.password)
    db_educator = Educator(
        email=educator_data.email,
        first_name=educator_data.first_name,
        last_name=educator_data.last_name,
        employee_id=employee_id,
        department=educator_data.department,
        title=educator_data.title,
        office_location=educator_data.office_location,
        phone=educator_data.phone,
        hashed_password=hashed_password
    )
    
    db.add(db_educator)
    db.commit()
    db.refresh(db_educator)
    
    return EducatorResponse(**db_educator.to_dict())

@router.post("/login", response_model=Token)
async def login_educator(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate educator and return access token"""
    educator = db.query(Educator).filter(Educator.email == form_data.username).first()
    
    if not educator or not verify_password(form_data.password, educator.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not educator.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Update last login
    from datetime import datetime
    educator.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": educator.email})
    
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=EducatorResponse)
async def get_current_educator_profile(current_educator: Educator = Depends(get_current_educator)):
    """Get current educator's profile"""
    return EducatorResponse(**current_educator.to_dict())

@router.put("/me", response_model=EducatorResponse)
async def update_educator_profile(
    educator_update: EducatorUpdate,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Update current educator's profile"""
    update_data = educator_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "notification_preferences" and value:
            setattr(current_educator, field, json.dumps(value))
        else:
            setattr(current_educator, field, value)
    
    db.commit()
    db.refresh(current_educator)
    
    return EducatorResponse(**current_educator.to_dict())

@router.get("/", response_model=List[EducatorResponse])
async def list_educators(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """List educators (admin only)"""
    if not current_educator.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    query = db.query(Educator)
    
    if department:
        query = query.filter(Educator.department == department)
    
    educators = query.offset(skip).limit(limit).all()
    
    return [EducatorResponse(**educator.to_dict()) for educator in educators]

@router.get("/{educator_id}", response_model=EducatorResponse)
async def get_educator(
    educator_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get educator by ID"""
    if educator_id != current_educator.id and not current_educator.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    educator = db.query(Educator).filter(Educator.id == educator_id).first()
    if not educator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Educator not found"
        )
    
    return EducatorResponse(**educator.to_dict())