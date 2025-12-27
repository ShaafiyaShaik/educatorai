"""
Teacher Dashboard API endpoints
Provides comprehensive dashboard functionality for teachers including sections, statistics, and management tools.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.api.students import get_filtered_section_students

router = APIRouter()
@router.get("/sections/{section_id}/students/filtered")
async def filtered_students_alias(
    section_id: int,
    pass_status: Optional[str] = None,
    subject_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Alias to match frontend path; proxies to students filtered handler."""
    return await get_filtered_section_students(
        section_id=section_id,
        pass_status=pass_status,
        subject_filter=subject_filter,
        search=search,
        current_educator=current_educator,
        db=db,
    )

# Pydantic models for responses
class StudentSummary(BaseModel):
    id: int
    student_id: str
    name: str
    email: str
    average_score: float
    status: str  # Pass/Fail
    total_subjects: int

class SectionSummary(BaseModel):
    id: int
    name: str
    total_students: int
    passed_students: int
    failed_students: int
    pass_rate: float
    average_score: float
    subject_averages: Dict[str, float]

class SubjectStatistics(BaseModel):
    subject_name: str
    total_students: int
    passed: int
    failed: int
    average_score: float
    highest_score: float
    lowest_score: float

class DashboardOverview(BaseModel):
    total_sections: int
    total_students: int
    total_passed: int
    total_failed: int
    overall_pass_rate: float
    overall_average: float
    sections: List[SectionSummary]
    recent_activity: List[Dict[str, Any]]

class StudentDetail(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    email: str
    section_name: str
    grades: List[Dict[str, Any]]
    average_score: float
    status: str
    created_at: str

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    status: str
    priority: str
    created_at: str
    read_at: Optional[str]

@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard overview for the current educator"""
    
    # Get all sections for this educator
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    
    if not sections:
        return DashboardOverview(
            total_sections=0,
            total_students=0,
            total_passed=0,
            total_failed=0,
            overall_pass_rate=0.0,
            overall_average=0.0,
            sections=[],
            recent_activity=[]
        )
    
    section_summaries = []
    total_students = 0
    total_passed = 0
    all_averages = []
    
    for section in sections:
        # Get students in this section with their grades
        students_query = db.query(Student).filter(Student.section_id == section.id)
        students = students_query.all()
        
        section_students_count = len(students)
        section_passed = 0
        section_averages = []
        subject_totals = {}
        
        for student in students:
            # Get all grades for this student
            grades = db.query(Grade).filter(Grade.student_id == student.id).all()
            
            if grades:
                student_total = sum(grade.marks_obtained for grade in grades)
                student_average = student_total / len(grades)
                section_averages.append(student_average)
                all_averages.append(student_average)
                
                # Check if student passed (average >= 40)
                if student_average >= 40:
                    section_passed += 1
                
                # Track subject averages
                for grade in grades:
                    subject = db.query(Subject).filter(Subject.id == grade.subject_id).first()
                    if subject:
                        if subject.name not in subject_totals:
                            subject_totals[subject.name] = []
                        subject_totals[subject.name].append(grade.marks_obtained)
        
        # Calculate section statistics
        section_average = sum(section_averages) / len(section_averages) if section_averages else 0
        section_pass_rate = (section_passed / section_students_count * 100) if section_students_count > 0 else 0
        
        # Calculate subject averages for this section
        subject_averages = {}
        for subject_name, scores in subject_totals.items():
            subject_averages[subject_name] = sum(scores) / len(scores) if scores else 0
        
        section_summary = SectionSummary(
            id=section.id,
            name=section.name,
            total_students=section_students_count,
            passed_students=section_passed,
            failed_students=section_students_count - section_passed,
            pass_rate=round(section_pass_rate, 1),
            average_score=round(section_average, 2),
            subject_averages=subject_averages
        )
        
        section_summaries.append(section_summary)
        total_students += section_students_count
        total_passed += section_passed
    
    # Calculate overall statistics
    total_failed = total_students - total_passed
    overall_pass_rate = (total_passed / total_students * 100) if total_students > 0 else 0
    overall_average = sum(all_averages) / len(all_averages) if all_averages else 0
    
    # Get recent activity (simplified for now)
    recent_activity = [
        {
            "type": "info",
            "message": f"Dashboard updated with {total_students} students across {len(sections)} sections",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    return DashboardOverview(
        total_sections=len(sections),
        total_students=total_students,
        total_passed=total_passed,
        total_failed=total_failed,
        overall_pass_rate=round(overall_pass_rate, 1),
        overall_average=round(overall_average, 2),
        sections=section_summaries,
        recent_activity=recent_activity
    )

@router.get("/sections", response_model=List[SectionSummary])
async def get_sections(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all sections for the current educator with statistics"""
    
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    section_summaries = []
    
    for section in sections:
        # Calculate section statistics (similar to dashboard logic)
        students = db.query(Student).filter(Student.section_id == section.id).all()
        
        passed_count = 0
        averages = []
        subject_totals = {}
        
        for student in students:
            grades = db.query(Grade).filter(Grade.student_id == student.id).all()
            if grades:
                student_avg = sum(g.marks_obtained for g in grades) / len(grades)
                averages.append(student_avg)
                if student_avg >= 40:
                    passed_count += 1
                
                for grade in grades:
                    subject = db.query(Subject).filter(Subject.id == grade.subject_id).first()
                    if subject:
                        if subject.name not in subject_totals:
                            subject_totals[subject.name] = []
                        subject_totals[subject.name].append(grade.marks_obtained)
        
        subject_averages = {name: sum(scores)/len(scores) for name, scores in subject_totals.items()}
        section_avg = sum(averages) / len(averages) if averages else 0
        pass_rate = (passed_count / len(students) * 100) if students else 0
        
        section_summaries.append(SectionSummary(
            id=section.id,
            name=section.name,
            total_students=len(students),
            passed_students=passed_count,
            failed_students=len(students) - passed_count,
            pass_rate=round(pass_rate, 1),
            average_score=round(section_avg, 2),
            subject_averages=subject_averages
        ))
    
    return section_summaries

@router.get("/sections/{section_id}/students", response_model=List[StudentDetail])
async def get_section_students(
    section_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name or student ID"),
    status_filter: Optional[str] = Query(None, description="Filter by Pass/Fail status"),
    sort_by: Optional[str] = Query("name", description="Sort by: name, average, status"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc, desc")
):
    """Get all students in a section with detailed information"""
    
    # Verify section belongs to current educator
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Get students with grades
    students_query = db.query(Student).filter(Student.section_id == section_id)
    
    # Apply search filter
    if search:
        students_query = students_query.filter(
            or_(
                Student.first_name.ilike(f"%{search}%"),
                Student.last_name.ilike(f"%{search}%"),
                Student.student_id.ilike(f"%{search}%")
            )
        )
    
    students = students_query.all()
    student_details = []
    
    for student in students:
        # Get grades for this student
        grades = db.query(Grade).join(Subject).filter(Grade.student_id == student.id).all()
        
        grade_details = []
        total_marks = 0
        grade_count = 0
        
        for grade in grades:
            subject = db.query(Subject).filter(Subject.id == grade.subject_id).first()
            if subject:
                grade_details.append({
                    "subject": subject.name,
                    "marks": grade.marks_obtained,
                    "total": grade.total_marks,
                    "percentage": grade.percentage,
                    "grade_letter": grade.grade_letter,
                    "passed": grade.is_passed
                })
                total_marks += grade.marks_obtained
                grade_count += 1
        
        average_score = total_marks / grade_count if grade_count > 0 else 0
        status = "Pass" if average_score >= 40 else "Fail"
        
        # Apply status filter
        if status_filter and status.lower() != status_filter.lower():
            continue
        
        student_detail = StudentDetail(
            id=student.id,
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            email=student.email,
            section_name=section.name,
            grades=grade_details,
            average_score=round(average_score, 2),
            status=status,
            created_at=student.created_at.isoformat() if student.created_at else ""
        )
        
        student_details.append(student_detail)
    
    # Apply sorting
    if sort_by == "average":
        student_details.sort(key=lambda x: x.average_score, reverse=(sort_order == "desc"))
    elif sort_by == "status":
        student_details.sort(key=lambda x: x.status, reverse=(sort_order == "desc"))
    else:  # default to name
        student_details.sort(key=lambda x: f"{x.first_name} {x.last_name}", reverse=(sort_order == "desc"))
    
    return student_details

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status: unread, read, archived"),
    limit: int = Query(20, description="Number of notifications to return")
):
    """Get notifications for the current educator"""
    
    query = db.query(Notification).filter(Notification.educator_id == current_educator.id)
    
    if status:
        try:
            status_enum = NotificationStatus(status.lower())
            query = query.filter(Notification.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    return [
        NotificationResponse(
            id=notif.id,
            title=notif.title,
            message=notif.message,
            type=notif.notification_type.value,
            status=notif.status.value,
            priority=notif.priority,
            created_at=notif.created_at.isoformat(),
            read_at=notif.read_at.isoformat() if notif.read_at else None
        )
        for notif in notifications
    ]

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.educator_id == current_educator.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.mark_as_read()
    notification.read_at = datetime.now()
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.get("/statistics/subjects", response_model=List[SubjectStatistics])
async def get_subject_statistics(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for each subject across all sections"""
    
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    section_ids = [s.id for s in sections]
    
    if not section_ids:
        return []
    
    # Get all subjects for educator's sections
    subjects = db.query(Subject).filter(Subject.section_id.in_(section_ids)).all()
    
    subject_stats = []
    
    for subject in subjects:
        # Get all grades for this subject
        grades = db.query(Grade).filter(Grade.subject_id == subject.id).all()
        
        if not grades:
            continue
        
        marks = [grade.marks_obtained for grade in grades]
        passed_count = sum(1 for mark in marks if mark >= 40)
        failed_count = len(marks) - passed_count
        
        subject_stats.append(SubjectStatistics(
            subject_name=subject.name,
            total_students=len(marks),
            passed=passed_count,
            failed=failed_count,
            average_score=round(sum(marks) / len(marks), 2),
            highest_score=max(marks),
            lowest_score=min(marks)
        ))
    
    return subject_stats