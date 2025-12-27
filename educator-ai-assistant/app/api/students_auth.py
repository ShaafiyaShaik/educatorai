"""
Student authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models.student import Student
from app.models.educator import Educator
from app.core.auth import verify_password, create_access_token
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class StudentLogin(BaseModel):
    email: EmailStr
    password: str

class StudentLoginResponse(BaseModel):
    access_token: str
    token_type: str
    student: dict

class StudentProfile(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    email: str
    roll_number: int
    section_name: str
    phone: str
    guardian_email: str
    is_active: bool

    class Config:
        from_attributes = True

# Authentication functions
def authenticate_student(db: Session, email: str, password: str):
    """Authenticate a student"""
    print(f"🔍 API authenticate_student called with email: {email}, password: {password}")
    
    student = db.query(Student).filter(Student.email == email).first()
    print(f"🔍 Student query result: {student}")
    
    if not student:
        print(f"❌ No student found with email: {email}")
        return False
        
    print(f"✅ Student found: {student.first_name} {student.last_name}")
    print(f"🔑 Stored hash: {student.password_hash[:50]}...")
    
    password_valid = verify_password(password, student.password_hash)
    print(f"🔐 Password verification result: {password_valid}")
    
    if not password_valid:
        print(f"❌ Password verification failed for {email}")
        return False
        
    print(f"✅ Authentication successful for {email}")
    return student

def get_current_student(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated student"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    student = db.query(Student).filter(Student.email == email).first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return student

# Endpoints
@router.post("/login", response_model=StudentLoginResponse)
async def login_student(student_data: StudentLogin, db: Session = Depends(get_db)):
    """Student login endpoint"""
    student = authenticate_student(db, student_data.email, student_data.password)
    if not student:
        # Helpful hint: if this is an educator email, direct user to educator login
        maybe_educator = db.query(Educator).filter(Educator.email == student_data.email).first()
        hint = "Incorrect email or password"
        if maybe_educator:
            hint = "This is an educator account. Please use /api/v1/educators/login or select 'Teacher' portal."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=hint,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "roll_number": student.roll_number,
            "section_name": student.section.name if student.section else None,
            "phone": student.phone,
            "guardian_email": student.guardian_email,
            "is_active": student.is_active
        }
    }

@router.get("/me", response_model=StudentProfile)
async def get_student_profile(current_student: Student = Depends(get_current_student)):
    """Get current student profile"""
    return StudentProfile(
        id=current_student.id,
        student_id=current_student.student_id,
        first_name=current_student.first_name,
        last_name=current_student.last_name,
        email=current_student.email,
        roll_number=current_student.roll_number,
        section_name=current_student.section.name if current_student.section else "No Section",
        phone=current_student.phone or "",
        guardian_email=current_student.guardian_email or "",
        is_active=current_student.is_active
    )