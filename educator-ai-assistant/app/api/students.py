"""
Student API endpoints for managing students, sections, and bulk operations
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade
from app.services.email_service import EmailService
import json

router = APIRouter()

# Pydantic models for request/response
class SectionResponse(BaseModel):
    id: int
    name: str
    academic_year: str
    semester: str
    student_count: int
    subjects: List[Dict[str, Any]]

class StudentResponse(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: Optional[str]
    guardian_email: Optional[str]
    is_active: bool

class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    credits: int
    passing_grade: float

class GradeResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    marks_obtained: float
    total_marks: float
    percentage: float
    grade_letter: str
    is_passed: bool
    student_name: str
    subject_name: str
    subject_code: str

class BulkEmailRequest(BaseModel):
    recipients: List[int]  # List of student IDs
    template_type: str  # "grades", "general", "custom"
    subject: str
    custom_message: Optional[str] = None
    include_grades: bool = False
    subject_filter: Optional[List[int]] = None  # Subject IDs for grade reports

class StudentWithGrades(BaseModel):
    student: StudentResponse
    grades: List[GradeResponse]
    overall_average: float
    passed_subjects: int
    failed_subjects: int

@router.get("/sections", response_model=List[SectionResponse])
async def get_my_sections(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all sections for the current educator"""
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    
    result = []
    for section in sections:
        # Get subject count and details
        subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        
        section_data = SectionResponse(
            id=section.id,
            name=section.name,
            academic_year=section.academic_year,
            semester=section.semester,
            student_count=student_count,
            subjects=[{
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "credits": s.credits,
                "passing_grade": s.passing_grade
            } for s in subjects]
        )
        result.append(section_data)
    
    return result

@router.get("/sections/{section_id}/students", response_model=List[StudentResponse])
async def get_section_students(
    section_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all students in a specific section"""
    # Verify section belongs to current educator
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    students = db.query(Student).filter(Student.section_id == section_id).all()
    
    return [StudentResponse(
        id=s.id,
        student_id=s.student_id,
        first_name=s.first_name,
        last_name=s.last_name,
        full_name=s.full_name,
        email=s.email,
        phone=s.phone,
        guardian_email=s.guardian_email,
        is_active=s.is_active
    ) for s in students]

@router.get("/students/{student_id}/grades", response_model=StudentWithGrades)
async def get_student_grades(
    student_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get detailed grades for a specific student"""
    # Verify student belongs to educator's section
    student = db.query(Student).join(Section).filter(
        Student.id == student_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get grades with subject information
    grades = db.query(Grade).join(Subject).filter(
        Grade.student_id == student_id
    ).options(joinedload(Grade.subject)).all()
    
    grade_responses = []
    total_percentage = 0
    passed_count = 0
    failed_count = 0
    
    for grade in grades:
        grade_responses.append(GradeResponse(
            id=grade.id,
            student_id=grade.student_id,
            subject_id=grade.subject_id,
            marks_obtained=grade.marks_obtained,
            total_marks=grade.total_marks,
            percentage=grade.percentage,
            grade_letter=grade.grade_letter,
            is_passed=grade.is_passed,
            student_name=student.full_name,
            subject_name=grade.subject.name,
            subject_code=grade.subject.code
        ))
        
        total_percentage += grade.percentage
        if grade.is_passed:
            passed_count += 1
        else:
            failed_count += 1
    
    overall_average = total_percentage / len(grades) if grades else 0
    
    return StudentWithGrades(
        student=StudentResponse(
            id=student.id,
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            full_name=student.full_name,
            email=student.email,
            phone=student.phone,
            guardian_email=student.guardian_email,
            is_active=student.is_active
        ),
        grades=grade_responses,
        overall_average=round(overall_average, 2),
        passed_subjects=passed_count,
        failed_subjects=failed_count
    )

class StudentWithGradesResponse(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: Optional[str]
    guardian_email: Optional[str]
    is_active: bool
    overall_average: float
    passed_subjects: int
    failed_subjects: int
    total_subjects: int
    is_overall_passed: bool
    grades: List[GradeResponse]

@router.get("/sections/{section_id}/students/filtered", response_model=List[StudentWithGradesResponse])
async def get_filtered_section_students(
    section_id: int,
    pass_status: Optional[str] = None,  # "passed", "failed", or None for all
    subject_filter: Optional[str] = None,  # e.g., "Math<40" or "Science>=80"
    search: Optional[str] = None,  # Search by name
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get filtered students in a section with their grades and performance"""
    
    # Debug logging
    print(f"DEBUG: section_id={section_id}, current_educator.id={current_educator.id}")
    
    # Verify section belongs to current educator
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == current_educator.id
    ).first()
    
    print(f"DEBUG: Section query result: {section}")
    
    if not section:
        # Additional debug: check if section exists at all
        any_section = db.query(Section).filter(Section.id == section_id).first()
        print(f"DEBUG: Section {section_id} exists but educator_id={any_section.educator_id if any_section else 'Not found'}")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Get all students in the section with their grades
    students_query = db.query(Student).filter(Student.section_id == section_id)
    
    # Apply name search filter
    if search:
        students_query = students_query.filter(
            (Student.first_name.ilike(f"%{search}%")) | 
            (Student.last_name.ilike(f"%{search}%"))
        )
    
    students = students_query.all()
    
    result = []
    for student in students:
        # Get grades for this student
        grades = db.query(Grade).join(Subject).filter(
            Grade.student_id == student.id
        ).options(joinedload(Grade.subject)).all()
        
        if not grades:
            continue
            
        grade_responses = []
        total_percentage = 0
        passed_count = 0
        failed_count = 0
        subject_scores = {}
        
        for grade in grades:
            grade_responses.append(GradeResponse(
                id=grade.id,
                student_id=grade.student_id,
                subject_id=grade.subject_id,
                marks_obtained=grade.marks_obtained,
                total_marks=grade.total_marks,
                percentage=grade.percentage,
                grade_letter=grade.grade_letter,
                is_passed=grade.is_passed,
                student_name=student.full_name,
                subject_name=grade.subject.name,
                subject_code=grade.subject.code
            ))
            
            total_percentage += grade.percentage
            subject_scores[grade.subject.name] = grade.percentage
            
            if grade.is_passed:
                passed_count += 1
            else:
                failed_count += 1
        
        overall_average = total_percentage / len(grades) if grades else 0
        is_overall_passed = passed_count > failed_count
        
        # Apply pass/fail filter
        if pass_status == "passed" and not is_overall_passed:
            continue
        elif pass_status == "failed" and is_overall_passed:
            continue
            
        # Apply subject performance filter (e.g., "Math<40")
        if subject_filter:
            try:
                if '<' in subject_filter:
                    subject_name, threshold = subject_filter.split('<')
                    threshold = float(threshold)
                    if subject_name.strip() in subject_scores:
                        if subject_scores[subject_name.strip()] >= threshold:
                            continue
                elif '>=' in subject_filter:
                    subject_name, threshold = subject_filter.split('>=')
                    threshold = float(threshold)
                    if subject_name.strip() in subject_scores:
                        if subject_scores[subject_name.strip()] < threshold:
                            continue
                elif '>' in subject_filter:
                    subject_name, threshold = subject_filter.split('>')
                    threshold = float(threshold)
                    if subject_name.strip() in subject_scores:
                        if subject_scores[subject_name.strip()] <= threshold:
                            continue
            except (ValueError, IndexError):
                # Invalid filter format, ignore
                pass
        
        result.append(StudentWithGradesResponse(
            id=student.id,
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            full_name=student.full_name,
            email=student.email,
            phone=student.phone,
            guardian_email=student.guardian_email,
            is_active=student.is_active,
            overall_average=round(overall_average, 2),
            passed_subjects=passed_count,
            failed_subjects=failed_count,
            total_subjects=len(grades),
            is_overall_passed=is_overall_passed,
            grades=grade_responses
        ))
    
    return result

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

class StudentProfileResponse(BaseModel):
    student: StudentWithGradesResponse
    notifications: List[NotificationResponse]
    attendance_summary: Dict[str, Any]
    communication_history: List[Dict[str, Any]]
    guardian_contacts: List[Dict[str, Any]]
    academic_progress: Dict[str, Any]

@router.get("/students/{student_id}/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    student_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get detailed student profile with all relevant information"""
    # Verify student belongs to educator's section
    student = db.query(Student).join(Section).filter(
        Student.id == student_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get grades with subject information
    grades = db.query(Grade).join(Subject).filter(
        Grade.student_id == student_id
    ).options(joinedload(Grade.subject)).all()
    
    grade_responses = []
    total_percentage = 0
    passed_count = 0
    failed_count = 0
    subject_performance = {}
    
    for grade in grades:
        grade_responses.append(GradeResponse(
            id=grade.id,
            student_id=grade.student_id,
            subject_id=grade.subject_id,
            marks_obtained=grade.marks_obtained,
            total_marks=grade.total_marks,
            percentage=grade.percentage,
            grade_letter=grade.grade_letter,
            is_passed=grade.is_passed,
            student_name=student.full_name,
            subject_name=grade.subject.name,
            subject_code=grade.subject.code
        ))
        
        total_percentage += grade.percentage
        subject_performance[grade.subject.name] = {
            "percentage": grade.percentage,
            "grade": grade.grade_letter,
            "passed": grade.is_passed,
            "marks": f"{grade.marks_obtained}/{grade.total_marks}"
        }
        
        if grade.is_passed:
            passed_count += 1
        else:
            failed_count += 1
    
    overall_average = total_percentage / len(grades) if grades else 0
    is_overall_passed = passed_count > failed_count
    
    # Create student with grades response
    student_with_grades = StudentWithGradesResponse(
        id=student.id,
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        full_name=student.full_name,
        email=student.email,
        phone=student.phone,
        guardian_email=student.guardian_email,
        is_active=student.is_active,
        overall_average=round(overall_average, 2),
        passed_subjects=passed_count,
        failed_subjects=failed_count,
        total_subjects=len(grades),
        is_overall_passed=is_overall_passed,
        grades=grade_responses
    )
    
    # Get notifications (mock for now)
    notifications = [
        NotificationResponse(
            id=1,
            title="Assignment Reminder",
            message="Your Math assignment is due tomorrow",
            type="assignment",
            is_read=False,
            created_at=datetime.now()
        ),
        NotificationResponse(
            id=2,
            title="Grade Update",
            message="Your Science test results are available",
            type="grade",
            is_read=True,
            created_at=datetime.now()
        )
    ]
    
    # Attendance summary (mock data)
    attendance_summary = {
        "total_classes": 45,
        "present": 42,
        "absent": 3,
        "attendance_percentage": round((42/45) * 100, 1),
        "recent_attendance": [
            {"date": "2024-01-15", "status": "present"},
            {"date": "2024-01-14", "status": "present"},
            {"date": "2024-01-13", "status": "absent"},
            {"date": "2024-01-12", "status": "present"},
            {"date": "2024-01-11", "status": "present"}
        ]
    }
    
    # Communication history (mock data)
    communication_history = [
        {
            "id": 1,
            "date": "2024-01-10",
            "type": "email",
            "subject": "Progress Update",
            "message": "Student showing good improvement in Math",
            "sent_to": "guardian"
        },
        {
            "id": 2,
            "date": "2024-01-05",
            "type": "notification",
            "subject": "Assignment Submitted",
            "message": "English essay submitted on time",
            "sent_to": "student"
        }
    ]
    
    # Guardian contacts
    guardian_contacts = [
        {
            "name": "Primary Guardian",
            "email": student.guardian_email or "guardian@example.com",
            "phone": "+1-234-567-8900",
            "relationship": "Parent",
            "is_primary": True
        }
    ]
    
    # Academic progress tracking
    academic_progress = {
        "current_term_performance": {
            "overall_grade": "B+",
            "gpa": round(overall_average / 20, 2),  # Convert percentage to 4.0 scale
            "class_rank": 15,
            "total_students": 50
        },
        "subject_performance": subject_performance,
        "improvement_areas": [
            subject for subject, perf in subject_performance.items() 
            if perf["percentage"] < 70
        ],
        "strengths": [
            subject for subject, perf in subject_performance.items() 
            if perf["percentage"] >= 85
        ],
        "trend": "improving" if overall_average > 75 else "needs_attention"
    }
    
    return StudentProfileResponse(
        student=student_with_grades,
        notifications=notifications,
        attendance_summary=attendance_summary,
        communication_history=communication_history,
        guardian_contacts=guardian_contacts,
        academic_progress=academic_progress
    )

@router.get("/sections/{section_id}/analytics")
async def get_section_analytics(
    section_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get analytics for a section (pass/fail rates, averages, etc.)"""
    # Verify section belongs to current educator
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Get subjects for this section
    subjects = db.query(Subject).filter(Subject.section_id == section_id).all()
    
    analytics = {
        "section_name": section.name,
        "total_students": db.query(Student).filter(Student.section_id == section_id).count(),
        "subjects": []
    }
    
    for subject in subjects:
        # Get grade statistics for this subject
        grades = db.query(Grade).filter(Grade.subject_id == subject.id).all()
        
        if grades:
            total_marks = sum(g.marks_obtained for g in grades)
            average_marks = total_marks / len(grades)
            passed_count = sum(1 for g in grades if g.is_passed)
            failed_count = len(grades) - passed_count
            
            subject_analytics = {
                "id": subject.id,
                "name": subject.name,
                "code": subject.code,
                "total_students": len(grades),
                "passed": passed_count,
                "failed": failed_count,
                "pass_rate": round((passed_count / len(grades)) * 100, 2),
                "average_marks": round(average_marks, 2),
                "highest_marks": max(g.marks_obtained for g in grades),
                "lowest_marks": min(g.marks_obtained for g in grades)
            }
        else:
            subject_analytics = {
                "id": subject.id,
                "name": subject.name,
                "code": subject.code,
                "total_students": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "average_marks": 0,
                "highest_marks": 0,
                "lowest_marks": 0
            }
        
        analytics["subjects"].append(subject_analytics)
    
    return analytics

async def send_bulk_email_task(
    recipients: List[Dict],
    subject: str,
    template_type: str,
    custom_message: str,
    educator_name: str,
    db: Session
):
    """Background task to send bulk emails"""
    email_service = EmailService()
    
    for recipient in recipients:
        try:
            # Prepare personalized email content
            if template_type == "grades":
                body = f"""Dear {recipient['student_name']},

Here are your recent academic results:

{recipient['grade_details']}

Overall Average: {recipient['overall_average']}%
Subjects Passed: {recipient['passed_subjects']}
Subjects Failed: {recipient['failed_subjects']}

{custom_message if custom_message else 'Please contact me if you have any questions about your results.'}

Best regards,
{educator_name}"""
            
            elif template_type == "general":
                body = f"""Dear {recipient['student_name']},

{custom_message}

Best regards,
{educator_name}"""
            
            else:  # custom
                body = f"""Dear {recipient['student_name']},

{custom_message}

Best regards,
{educator_name}"""
            
            # Send email
            result = await email_service.send_email(
                recipient_email=recipient['email'],
                subject=subject,
                body=body,
                sender_email=f"{educator_name.lower().replace(' ', '.')}@university.edu"
            )
            
            print(f"Email sent to {recipient['email']}: {result['status']}")
            
        except Exception as e:
            print(f"Failed to send email to {recipient['email']}: {str(e)}")

@router.post("/bulk-email")
async def send_bulk_email(
    request: BulkEmailRequest,
    background_tasks: BackgroundTasks,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Send bulk personalized emails to selected students"""
    
    # Get students and verify they belong to educator's sections
    students = db.query(Student).join(Section).filter(
        Student.id.in_(request.recipients),
        Section.educator_id == current_educator.id
    ).all()
    
    if len(students) != len(request.recipients):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some students not found or don't belong to your sections"
        )
    
    # Prepare recipient data
    recipients = []
    for student in students:
        recipient_data = {
            "student_name": student.full_name,
            "email": student.email,
            "guardian_email": student.guardian_email
        }
        
        # Add grade information if requested
        if request.include_grades:
            grades_query = db.query(Grade).join(Subject).filter(
                Grade.student_id == student.id
            )
            
            # Filter by subjects if specified
            if request.subject_filter:
                grades_query = grades_query.filter(Subject.id.in_(request.subject_filter))
            
            grades = grades_query.options(joinedload(Grade.subject)).all()
            
            grade_details = []
            total_percentage = 0
            passed_count = 0
            failed_count = 0
            
            for grade in grades:
                grade_details.append(f"  • {grade.subject.name} ({grade.subject.code}): {grade.marks_obtained}/{grade.total_marks} ({grade.percentage:.1f}%) - {grade.grade_letter}")
                total_percentage += grade.percentage
                if grade.is_passed:
                    passed_count += 1
                else:
                    failed_count += 1
            
            recipient_data.update({
                "grade_details": "\n".join(grade_details),
                "overall_average": round(total_percentage / len(grades) if grades else 0, 2),
                "passed_subjects": passed_count,
                "failed_subjects": failed_count
            })
        
        recipients.append(recipient_data)
    
    # Start background task to send emails
    background_tasks.add_task(
        send_bulk_email_task,
        recipients,
        request.subject,
        request.template_type,
        request.custom_message or "",
        current_educator.full_name,
        db
    )
    
    return {
        "message": f"Bulk email job started for {len(recipients)} recipients",
        "recipients_count": len(recipients),
        "template_type": request.template_type
    }