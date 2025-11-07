"""
Teacher Dashboard API endpoints
Provides dashboard statistics and section overview for teachers
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Dict, Any
from pydantic import BaseModel
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade

router = APIRouter()

# Pydantic models for response
class SectionStats(BaseModel):
    section_id: int
    section_name: str
    total_students: int
    passed_students: int
    failed_students: int
    pass_rate: float
    section_average: float
    subjects_average: Dict[str, float]

class OverallStats(BaseModel):
    total_students: int
    total_passed: int
    total_failed: int
    overall_pass_rate: float
    overall_average: float
    total_sections: int

class DashboardResponse(BaseModel):
    teacher_name: str
    teacher_email: str
    overall_stats: OverallStats
    sections: List[SectionStats]

def calculate_student_average(student_id: int, db: Session) -> float:
    """Calculate average score for a student across all subjects"""
    grades = db.query(Grade).filter(Grade.student_id == student_id).all()
    if not grades:
        return 0.0
    
    total_marks = sum(grade.marks_obtained for grade in grades)
    return round(total_marks / len(grades), 2)

def is_student_passed(student_id: int, db: Session) -> bool:
    """Determine if student passed based on average >= 40"""
    average = calculate_student_average(student_id, db)
    return average >= 40.0

@router.get("/dashboard", response_model=DashboardResponse)
async def get_teacher_dashboard(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get complete dashboard data for the current teacher"""
    
    # Get all sections for this teacher
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    
    if not sections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sections found for this teacher"
        )
    
    sections_stats = []
    total_students_all = 0
    total_passed_all = 0
    total_failed_all = 0
    all_averages = []
    
    for section in sections:
        # Get all students in this section
        students = db.query(Student).filter(Student.section_id == section.id).all()
        
        if not students:
            continue
        
        # Calculate statistics for this section
        section_students_count = len(students)
        passed_count = 0
        failed_count = 0
        section_averages = []
        
        # Calculate subject averages
        subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
        subject_averages = {}
        
        for subject in subjects:
            # Get all grades for this subject in this section
            subject_grades = db.query(Grade).join(Student).filter(
                Student.section_id == section.id,
                Grade.subject_id == subject.id
            ).all()
            
            if subject_grades:
                avg_marks = sum(grade.marks_obtained for grade in subject_grades) / len(subject_grades)
                subject_averages[subject.name] = round(avg_marks, 2)
        
        # Calculate pass/fail for each student
        for student in students:
            student_average = calculate_student_average(student.id, db)
            section_averages.append(student_average)
            
            if is_student_passed(student.id, db):
                passed_count += 1
            else:
                failed_count += 1
        
        # Calculate section average
        section_average = round(sum(section_averages) / len(section_averages), 2) if section_averages else 0.0
        pass_rate = round((passed_count / section_students_count) * 100, 1) if section_students_count > 0 else 0.0
        
        # Add to overall totals
        total_students_all += section_students_count
        total_passed_all += passed_count
        total_failed_all += failed_count
        all_averages.extend(section_averages)
        
        # Create section stats
        section_stats = SectionStats(
            section_id=section.id,
            section_name=section.name,
            total_students=section_students_count,
            passed_students=passed_count,
            failed_students=failed_count,
            pass_rate=pass_rate,
            section_average=section_average,
            subjects_average=subject_averages
        )
        
        sections_stats.append(section_stats)
    
    # Calculate overall statistics
    overall_average = round(sum(all_averages) / len(all_averages), 2) if all_averages else 0.0
    overall_pass_rate = round((total_passed_all / total_students_all) * 100, 1) if total_students_all > 0 else 0.0
    
    overall_stats = OverallStats(
        total_students=total_students_all,
        total_passed=total_passed_all,
        total_failed=total_failed_all,
        overall_pass_rate=overall_pass_rate,
        overall_average=overall_average,
        total_sections=len(sections)
    )
    
    return DashboardResponse(
        teacher_name=current_educator.full_name,
        teacher_email=current_educator.email,
        overall_stats=overall_stats,
        sections=sections_stats
    )

@router.get("/sections", response_model=List[SectionStats])
async def get_teacher_sections(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all sections for the current teacher with basic stats"""
    
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    
    sections_stats = []
    for section in sections:
        students = db.query(Student).filter(Student.section_id == section.id).all()
        
        if not students:
            continue
        
        passed_count = sum(1 for student in students if is_student_passed(student.id, db))
        failed_count = len(students) - passed_count
        
        # Calculate section average
        averages = [calculate_student_average(student.id, db) for student in students]
        section_average = round(sum(averages) / len(averages), 2) if averages else 0.0
        pass_rate = round((passed_count / len(students)) * 100, 1) if students else 0.0
        
        # Get subject averages
        subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
        subject_averages = {}
        
        for subject in subjects:
            subject_grades = db.query(Grade).join(Student).filter(
                Student.section_id == section.id,
                Grade.subject_id == subject.id
            ).all()
            
            if subject_grades:
                avg_marks = sum(grade.marks_obtained for grade in subject_grades) / len(subject_grades)
                subject_averages[subject.name] = round(avg_marks, 2)
        
        section_stats = SectionStats(
            section_id=section.id,
            section_name=section.name,
            total_students=len(students),
            passed_students=passed_count,
            failed_students=failed_count,
            pass_rate=pass_rate,
            section_average=section_average,
            subjects_average=subject_averages
        )
        
        sections_stats.append(section_stats)
    
    return sections_stats

@router.get("/sections/{section_id}/preview")
async def get_section_preview(
    section_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get a preview of students in a specific section"""
    
    # Verify section belongs to current teacher
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found or access denied"
        )
    
    # Get first 5 students as preview
    students = db.query(Student).filter(Student.section_id == section_id).limit(5).all()
    
    student_previews = []
    for student in students:
        average = calculate_student_average(student.id, db)
        status = "Pass" if is_student_passed(student.id, db) else "Fail"
        
        student_previews.append({
            "student_id": student.student_id,
            "name": student.full_name,
            "email": student.email,
            "average": average,
            "status": status
        })
    
    total_students = db.query(Student).filter(Student.section_id == section_id).count()
    
    return {
        "section_id": section.id,
        "section_name": section.name,
        "total_students": total_students,
        "preview_students": student_previews,
        "showing": f"Showing {len(student_previews)} of {total_students} students"
    }