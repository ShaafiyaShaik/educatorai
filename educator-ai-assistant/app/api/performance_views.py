"""
Enhanced Performance Views API
Provides comprehensive performance analytics with filtering, sorting, and reporting capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel
from datetime import datetime, timedelta
import io
import pandas as pd
import json
import asyncio
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade
from app.models.report import SentReport, ReportType, RecipientType, ReportStatus
from app.models.performance import Attendance, Exam
from app.models.notification import Notification, NotificationType

router = APIRouter()

# Enhanced Pydantic Models
class StudentPerformanceDetail(BaseModel):
    id: int
    student_id: str
    name: str
    email: str
    section_name: str
    roll_number: int
    average_score: float
    status: str
    attendance_percentage: Optional[float] = 85.0  # Mock data for now
    total_subjects: int
    passed_subjects: int
    failed_subjects: int
    subject_grades: List[Dict[str, Any]]

class SectionPerformanceView(BaseModel):
    section_id: int
    section_name: str
    total_students: int
    passed_students: int
    failed_students: int
    pass_rate: float
    average_score: float
    highest_score: float
    lowest_score: float
    attendance_average: float
    subject_averages: Dict[str, float]
    top_performers: List[StudentPerformanceDetail]
    low_performers: List[StudentPerformanceDetail]

class SubjectPerformanceView(BaseModel):
    subject_id: int
    subject_name: str
    subject_code: str
    total_students: int
    passed_students: int
    failed_students: int
    pass_rate: float
    average_score: float
    highest_score: float
    lowest_score: float
    grade_distribution: Dict[str, int]  # A+: 5, A: 10, B+: 8, etc.
    sections_performance: List[Dict[str, Any]]

class OverallPerformanceView(BaseModel):
    total_sections: int
    total_students: int
    total_subjects: int
    overall_pass_rate: float
    overall_average: float
    sections_summary: List[SectionPerformanceView]
    subjects_summary: List[SubjectPerformanceView]
    grade_level_stats: Dict[str, Any]
    top_performers: List[StudentPerformanceDetail]
    low_performers: List[StudentPerformanceDetail]
    # New chart data fields
    grade_distribution: Dict[str, int] = {}  # A+: 15, A: 25, B+: 20, etc.
    subject_performance_chart: List[Dict[str, Any]] = []  # Chart data for subjects
    sections_performance_chart: List[Dict[str, Any]] = []  # Chart data for sections
    attendance_stats: Dict[str, Any] = {}
    monthly_trends: List[Dict[str, Any]] = []

class PerformanceFilter(BaseModel):
    view_type: Literal["section", "subject", "overall", "student"] = "overall"
    section_ids: Optional[List[int]] = None
    subject_ids: Optional[List[int]] = None
    performance_threshold: Optional[float] = None  # Filter by minimum percentage
    sort_by: Literal["name", "average", "attendance", "pass_rate"] = "average"
    sort_order: Literal["asc", "desc"] = "desc"
    include_top_performers: bool = True
    include_low_performers: bool = True
    top_count: int = 5
    low_count: int = 5

# Helper Functions
def calculate_student_performance_detailed(student: Student, db: Session) -> StudentPerformanceDetail:
    """Calculate detailed performance metrics for a student"""
    # Get all grades for the student
    grades = db.query(Grade).options(joinedload(Grade.subject)).filter(
        Grade.student_id == student.id
    ).all()
    
    if not grades:
        return StudentPerformanceDetail(
            id=student.id,
            student_id=student.student_id,
            name=student.full_name,
            email=student.email,
            section_name=student.section.name,
            roll_number=student.roll_number,
            average_score=0.0,
            status="No Data",
            total_subjects=0,
            passed_subjects=0,
            failed_subjects=0,
            subject_grades=[]
        )
    
    # Calculate metrics
    total_marks = sum(grade.marks_obtained for grade in grades)
    total_possible = sum(grade.total_marks for grade in grades)
    average_score = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    passed_subjects = sum(1 for grade in grades if grade.percentage >= 60)
    failed_subjects = len(grades) - passed_subjects
    status = "Pass" if average_score >= 60 else "Fail"
    
    # Subject grades detail
    subject_grades = []
    for grade in grades:
        subject_grades.append({
            "subject_name": grade.subject.name,
            "subject_code": grade.subject.code,
            "marks_obtained": grade.marks_obtained,
            "total_marks": grade.total_marks,
            "percentage": grade.percentage or (grade.marks_obtained / grade.total_marks * 100),
            "grade_letter": grade.grade_letter,
            "is_passed": grade.percentage >= 60 if grade.percentage else False
        })
    
    return StudentPerformanceDetail(
        id=student.id,
        student_id=student.student_id,
        name=student.full_name,
        email=student.email,
        section_name=student.section.name,
        roll_number=student.roll_number,
        average_score=round(average_score, 2),
        status=status,
        total_subjects=len(grades),
        passed_subjects=passed_subjects,
        failed_subjects=failed_subjects,
        subject_grades=subject_grades
    )

def get_section_performance(section_id: int, db: Session, educator_id: int) -> SectionPerformanceView:
    """Get comprehensive performance data for a section"""
    # Verify section belongs to educator
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == educator_id
    ).first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Get all students in section
    students = db.query(Student).options(joinedload(Student.section)).filter(
        Student.section_id == section_id
    ).all()
    
    if not students:
        return SectionPerformanceView(
            section_id=section_id,
            section_name=section.name,
            total_students=0,
            passed_students=0,
            failed_students=0,
            pass_rate=0.0,
            average_score=0.0,
            highest_score=0.0,
            lowest_score=0.0,
            attendance_average=0.0,
            subject_averages={},
            top_performers=[],
            low_performers=[]
        )
    
    # Calculate performance for each student
    student_performances = []
    for student in students:
        performance = calculate_student_performance_detailed(student, db)
        student_performances.append(performance)
    
    # Calculate section metrics
    scores = [p.average_score for p in student_performances if p.average_score > 0]
    passed_students = sum(1 for p in student_performances if p.status == "Pass")
    failed_students = len(student_performances) - passed_students
    pass_rate = (passed_students / len(student_performances) * 100) if student_performances else 0
    average_score = sum(scores) / len(scores) if scores else 0
    highest_score = max(scores) if scores else 0
    lowest_score = min(scores) if scores else 0
    
    # Calculate subject averages
    subjects = db.query(Subject).filter(Subject.section_id == section_id).all()
    subject_averages = {}
    for subject in subjects:
        subject_grades = db.query(Grade).filter(
            Grade.subject_id == subject.id,
            Grade.student_id.in_([s.id for s in students])
        ).all()
        if subject_grades:
            subject_avg = sum(g.percentage or (g.marks_obtained / g.total_marks * 100) 
                            for g in subject_grades) / len(subject_grades)
            subject_averages[subject.name] = round(subject_avg, 2)
    
    # Get top and low performers
    sorted_performances = sorted(student_performances, key=lambda x: x.average_score, reverse=True)
    top_performers = sorted_performances[:5]
    low_performers = sorted_performances[-5:][::-1]  # Reverse to show lowest first
    
    return SectionPerformanceView(
        section_id=section_id,
        section_name=section.name,
        total_students=len(students),
        passed_students=passed_students,
        failed_students=failed_students,
        pass_rate=round(pass_rate, 2),
        average_score=round(average_score, 2),
        highest_score=round(highest_score, 2),
        lowest_score=round(lowest_score, 2),
        attendance_average=85.0,  # Mock data
        subject_averages=subject_averages,
        top_performers=top_performers,
        low_performers=low_performers
    )

def get_subject_performance(subject_id: int, db: Session, educator_id: int) -> SubjectPerformanceView:
    """Get comprehensive performance data for a subject"""
    # Get subject and verify it belongs to educator's sections
    subject = db.query(Subject).options(joinedload(Subject.section)).filter(
        Subject.id == subject_id,
        Subject.section.has(Section.educator_id == educator_id)
    ).first()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Get all grades for this subject
    grades = db.query(Grade).options(
        joinedload(Grade.student).joinedload(Student.section)
    ).filter(Grade.subject_id == subject_id).all()
    
    if not grades:
        return SubjectPerformanceView(
            subject_id=subject_id,
            subject_name=subject.name,
            subject_code=subject.code,
            total_students=0,
            passed_students=0,
            failed_students=0,
            pass_rate=0.0,
            average_score=0.0,
            highest_score=0.0,
            lowest_score=0.0,
            grade_distribution={},
            sections_performance=[]
        )
    
    # Calculate metrics
    percentages = [g.percentage or (g.marks_obtained / g.total_marks * 100) for g in grades]
    passed_students = sum(1 for p in percentages if p >= 60)
    failed_students = len(percentages) - passed_students
    pass_rate = (passed_students / len(percentages) * 100) if percentages else 0
    average_score = sum(percentages) / len(percentages) if percentages else 0
    highest_score = max(percentages) if percentages else 0
    lowest_score = min(percentages) if percentages else 0
    
    # Grade distribution
    grade_distribution = {"A+": 0, "A": 0, "B+": 0, "B": 0, "C+": 0, "C": 0, "D+": 0, "D": 0, "F": 0}
    for grade in grades:
        if grade.grade_letter:
            grade_distribution[grade.grade_letter] = grade_distribution.get(grade.grade_letter, 0) + 1
    
    # Section-wise performance for this subject
    sections_performance = []
    section_grades = {}
    for grade in grades:
        section_name = grade.student.section.name
        if section_name not in section_grades:
            section_grades[section_name] = []
        section_grades[section_name].append(grade.percentage or (grade.marks_obtained / grade.total_marks * 100))
    
    for section_name, section_percentages in section_grades.items():
        sections_performance.append({
            "section_name": section_name,
            "total_students": len(section_percentages),
            "average_score": round(sum(section_percentages) / len(section_percentages), 2),
            "passed_students": sum(1 for p in section_percentages if p >= 60),
            "pass_rate": round(sum(1 for p in section_percentages if p >= 60) / len(section_percentages) * 100, 2)
        })
    
    return SubjectPerformanceView(
        subject_id=subject_id,
        subject_name=subject.name,
        subject_code=subject.code,
        total_students=len(grades),
        passed_students=passed_students,
        failed_students=failed_students,
        pass_rate=round(pass_rate, 2),
        average_score=round(average_score, 2),
        highest_score=round(highest_score, 2),
        lowest_score=round(lowest_score, 2),
        grade_distribution=grade_distribution,
        sections_performance=sections_performance
    )

# API Endpoints
@router.get("/overview", response_model=OverallPerformanceView)
async def get_overall_performance(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get comprehensive overall performance view"""
    
    # Get all sections for this educator
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    
    if not sections:
        return OverallPerformanceView(
            total_sections=0,
            total_students=0,
            total_subjects=0,
            overall_pass_rate=0.0,
            overall_average=0.0,
            sections_summary=[],
            subjects_summary=[],
            grade_level_stats={}
        )
    
    # Get sections summary
    sections_summary = []
    total_students = 0
    total_passed = 0
    all_scores = []
    
    for section in sections:
        section_perf = get_section_performance(section.id, db, current_educator.id)
        sections_summary.append(section_perf)
        total_students += section_perf.total_students
        total_passed += section_perf.passed_students
        if section_perf.average_score > 0:
            all_scores.extend([section_perf.average_score] * section_perf.total_students)
    
    # Get subjects summary
    subjects = db.query(Subject).filter(
        Subject.section_id.in_([s.id for s in sections])
    ).all()
    
    subjects_summary = []
    for subject in subjects:
        subject_perf = get_subject_performance(subject.id, db, current_educator.id)
        subjects_summary.append(subject_perf)
    
    # Calculate overall metrics
    overall_pass_rate = (total_passed / total_students * 100) if total_students > 0 else 0
    overall_average = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Grade level statistics
    grade_level_stats = {
        "excellent": sum(1 for score in all_scores if score >= 90),
        "good": sum(1 for score in all_scores if 75 <= score < 90),
        "average": sum(1 for score in all_scores if 60 <= score < 75),
        "below_average": sum(1 for score in all_scores if score < 60),
    }
    
    # Get top and low performers from all sections
    all_top_performers = []
    all_low_performers = []
    
    for section_perf in sections_summary:
        all_top_performers.extend(section_perf.top_performers)
        all_low_performers.extend(section_perf.low_performers)
    
    # Sort and limit to top 5 each
    all_top_performers.sort(key=lambda x: x.average_score, reverse=True)
    all_low_performers.sort(key=lambda x: x.average_score)
    
    top_performers = all_top_performers[:5]
    low_performers = all_low_performers[:5]
    
    # Calculate Grade Distribution for chart
    grade_distribution = {}
    if all_scores:
        for score in all_scores:
            if score >= 97:
                grade = "A+"
            elif score >= 93:
                grade = "A"
            elif score >= 90:
                grade = "A-"
            elif score >= 87:
                grade = "B+"
            elif score >= 83:
                grade = "B"
            elif score >= 80:
                grade = "B-"
            elif score >= 77:
                grade = "C+"
            elif score >= 73:
                grade = "C"
            elif score >= 70:
                grade = "C-"
            elif score >= 67:
                grade = "D+"
            elif score >= 60:
                grade = "D"
            else:
                grade = "F"
            
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
    
    # Subject Performance Chart Data
    subject_performance_chart = []
    for subject_perf in subjects_summary:
        subject_performance_chart.append({
            "name": subject_perf.subject_name,
            "average": round(subject_perf.average_score, 1),
            "pass_rate": round(subject_perf.pass_rate, 1),
            "students": subject_perf.total_students
        })
    
    # Sections Performance Chart Data
    sections_performance_chart = []
    for section_perf in sections_summary:
        sections_performance_chart.append({
            "name": section_perf.section_name,
            "average": round(section_perf.average_score, 1),
            "pass_rate": round(section_perf.pass_rate, 1),
            "students": section_perf.total_students,
            "attendance": round(section_perf.attendance_average, 1)
        })
    
    # Attendance Stats
    attendance_stats = {
        "overall_attendance": 85.5,  # Calculate from real data if available
        "trend": "increasing",
        "weekly_average": [82, 84, 86, 85, 87]  # Mock weekly data
    }
    
    # Monthly Trends (Mock data - replace with real historical data)
    monthly_trends = [
        {"month": "Sep", "average": 78.2, "attendance": 83.1},
        {"month": "Oct", "average": 80.1, "attendance": 85.3},
        {"month": "Nov", "average": 81.5, "attendance": 86.2},
        {"month": "Dec", "average": 79.8, "attendance": 84.7}
    ]
    
    return OverallPerformanceView(
        total_sections=len(sections),
        total_students=total_students,
        total_subjects=len(subjects),
        overall_pass_rate=round(overall_pass_rate, 2),
        overall_average=round(overall_average, 2),
        sections_summary=sections_summary,
        subjects_summary=subjects_summary,
        grade_level_stats=grade_level_stats,
        top_performers=top_performers,
        low_performers=low_performers,
        grade_distribution=grade_distribution,
        subject_performance_chart=subject_performance_chart,
        sections_performance_chart=sections_performance_chart,
        attendance_stats=attendance_stats,
        monthly_trends=monthly_trends
    )

@router.get("/section/{section_id}", response_model=SectionPerformanceView)
async def get_section_performance_view(
    section_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get detailed performance view for a specific section"""
    return get_section_performance(section_id, db, current_educator.id)

@router.get("/subject/{subject_id}", response_model=SubjectPerformanceView)
async def get_subject_performance_view(
    subject_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get detailed performance view for a specific subject"""
    return get_subject_performance(subject_id, db, current_educator.id)

@router.post("/filtered")
async def get_filtered_performance(
    filters: PerformanceFilter,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get performance data with advanced filtering and sorting"""
    
    # Base query for students in educator's sections
    students_query = db.query(Student).options(
        joinedload(Student.section),
        joinedload(Student.grades).joinedload(Grade.subject)
    ).filter(Student.section.has(Section.educator_id == current_educator.id))
    
    # Apply section filter
    if filters.section_ids:
        students_query = students_query.filter(Student.section_id.in_(filters.section_ids))
    
    students = students_query.all()
    
    # Calculate performance for each student
    student_performances = []
    for student in students:
        performance = calculate_student_performance_detailed(student, db)
        
        # Apply performance threshold filter
        if filters.performance_threshold and performance.average_score < filters.performance_threshold:
            continue
            
        student_performances.append(performance)
    
    # Apply sorting
    reverse_order = filters.sort_order == "desc"
    if filters.sort_by == "name":
        student_performances.sort(key=lambda x: x.full_name, reverse=reverse_order)
    elif filters.sort_by == "average":
        student_performances.sort(key=lambda x: x.average_score, reverse=reverse_order)
    elif filters.sort_by == "attendance":
        student_performances.sort(key=lambda x: x.attendance_percentage or 0, reverse=reverse_order)
    
    # Filter top/low performers if requested
    result = {
        "students": student_performances,
        "total_count": len(student_performances),
        "filters_applied": filters.dict()
    }
    
    if filters.include_top_performers and filters.view_type != "student":
        top_performers = sorted(student_performances, key=lambda x: x.average_score, reverse=True)[:filters.top_count]
        result["top_performers"] = top_performers
    
    if filters.include_low_performers and filters.view_type != "student":
        low_performers = sorted(student_performances, key=lambda x: x.average_score)[:filters.low_count]
        result["low_performers"] = low_performers
    
    return result

@router.get("/student/{student_id}", response_model=StudentPerformanceDetail)
async def get_student_performance_detail(
    student_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get detailed performance data for a specific student"""
    
    # Verify student belongs to educator's sections
    student = db.query(Student).options(
        joinedload(Student.section),
        joinedload(Student.grades).joinedload(Grade.subject)
    ).filter(
        Student.id == student_id,
        Student.section.has(Section.educator_id == current_educator.id)
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return calculate_student_performance_detailed(student, db)

# Alias endpoint for frontend compatibility
@router.get("/student-details/{student_id}", response_model=StudentPerformanceDetail)
async def get_student_details(
    student_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Alias for get_student_performance_detail for frontend compatibility"""
    return await get_student_performance_detail(student_id, current_educator, db)

# Report Generation Endpoints
@router.get("/reports/download")
async def download_performance_report(
    format: Literal["pdf", "excel"] = Query("pdf"),
    view_type: Literal["section", "subject", "overall"] = Query("overall"),
    section_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Download comprehensive performance report in PDF or Excel format"""
    
    if format == "pdf":
        return await generate_pdf_report(view_type, section_id, subject_id, current_educator, db)
    elif format == "excel":
        return await generate_excel_report(view_type, section_id, subject_id, current_educator, db)

async def generate_pdf_report(view_type: str, section_id: Optional[int], subject_id: Optional[int], 
                            educator: Educator, db: Session) -> FileResponse:
    """Generate PDF performance report based on view type"""
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    # Generate different reports based on view type
    if view_type == "overall":
        # OVERALL PERFORMANCE REPORT
        title = f"Overall Performance Report - {educator.first_name} {educator.last_name}"
        
        # Get overall performance data directly (without FastAPI dependencies)
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        
        if not sections:
            # Create empty data structure
            data = OverallPerformanceView(
                total_sections=0,
                total_students=0,
                total_subjects=0,
                overall_pass_rate=0.0,
                overall_average=0.0,
                sections_summary=[],
                subjects_summary=[],
                grade_level_stats={}
            )
        else:
            # Calculate performance metrics
            sections_summary = []
            total_students = 0
            total_passed = 0
            all_scores = []
            
            for section in sections:
                section_perf = get_section_performance(section.id, db, educator.id)
                sections_summary.append(section_perf)
                total_students += section_perf.total_students
                total_passed += section_perf.passed_students
                if section_perf.average_score > 0:
                    all_scores.extend([section_perf.average_score] * section_perf.total_students)
            
            # Get subjects summary
            subjects = db.query(Subject).filter(
                Subject.section_id.in_([s.id for s in sections])
            ).all()
            
            subjects_summary = []
            for subject in subjects:
                subject_perf = get_subject_performance(subject.id, db, educator.id)
                subjects_summary.append(subject_perf)
            
            # Calculate overall metrics
            overall_pass_rate = (total_passed / total_students * 100) if total_students > 0 else 0
            overall_average = sum(all_scores) / len(all_scores) if all_scores else 0
            
            # Grade level statistics
            grade_level_stats = {
                "excellent": sum(1 for score in all_scores if score >= 90),
                "good": sum(1 for score in all_scores if 75 <= score < 90),
                "average": sum(1 for score in all_scores if 60 <= score < 75),
                "below_average": sum(1 for score in all_scores if score < 60),
            }
            
            # Get top and low performers (simplified for PDF generation)
            top_performers = []
            low_performers = []
            
            data = OverallPerformanceView(
                total_sections=len(sections),
                total_students=total_students,
                total_subjects=len(subjects),
                overall_pass_rate=round(overall_pass_rate, 2),
                overall_average=round(overall_average, 2),
                sections_summary=sections_summary,
                subjects_summary=subjects_summary,
                grade_level_stats=grade_level_stats,
                top_performers=top_performers,
                low_performers=low_performers
            )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_data = [
            ['Metric', 'Value', 'Status'],
            ['Total Sections', str(data.total_sections), '✓'],
            ['Total Students', str(data.total_students), '✓'],
            ['Total Subjects', str(data.total_subjects), '✓'],
            ['Overall Pass Rate', f"{data.overall_pass_rate}%", '✓' if data.overall_pass_rate >= 70 else '⚠'],
            ['Overall Average', f"{data.overall_average}%", '✓' if data.overall_average >= 75 else '⚠']
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Grade Distribution
        if data.grade_level_stats:
            story.append(Paragraph("Grade Distribution Analysis", styles['Heading2']))
            grade_data = [
                ['Performance Level', 'Count', 'Percentage'],
                ['Excellent (90%+)', str(data.grade_level_stats.get('excellent', 0)), 
                 f"{(data.grade_level_stats.get('excellent', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"],
                ['Good (75-89%)', str(data.grade_level_stats.get('good', 0)),
                 f"{(data.grade_level_stats.get('good', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"],
                ['Average (60-74%)', str(data.grade_level_stats.get('average', 0)),
                 f"{(data.grade_level_stats.get('average', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"],
                ['Below Average (<60%)', str(data.grade_level_stats.get('below_average', 0)),
                 f"{(data.grade_level_stats.get('below_average', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"]
            ]
            
            grade_table = Table(grade_data)
            grade_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen)
            ]))
            story.append(grade_table)
            story.append(Spacer(1, 20))
        
        # Sections Performance Comparison
        if data.sections_summary:
            story.append(Paragraph("Sections Performance Comparison", styles['Heading2']))
            sections_data = [['Section', 'Students', 'Pass Rate', 'Average', 'Highest', 'Lowest']]
            for section in data.sections_summary:
                sections_data.append([
                    section.section_name,
                    str(section.total_students),
                    f"{section.pass_rate}%",
                    f"{section.average_score}%",
                    f"{section.highest_score}%",
                    f"{section.lowest_score}%"
                ])
            
            sections_table = Table(sections_data)
            sections_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender)
            ]))
            story.append(sections_table)
    
    elif view_type == "section" and section_id:
        # SECTION ANALYSIS REPORT
        section = db.query(Section).filter(Section.id == section_id).first()
        title = f"Section Analysis Report - {section.name if section else 'Unknown Section'}"
        data = get_section_performance(section_id, db, educator.id)
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Section Overview
        story.append(Paragraph("Section Overview", styles['Heading2']))
        overview_data = [
            ['Section Details', 'Value'],
            ['Section Name', data.section_name],
            ['Total Students', str(data.total_students)],
            ['Students Passed', str(data.passed_students)],
            ['Students Failed', str(data.failed_students)],
            ['Pass Rate', f"{data.pass_rate}%"],
            ['Class Average', f"{data.average_score}%"],
            ['Highest Score', f"{data.highest_score}%"],
            ['Lowest Score', f"{data.lowest_score}%"],
            ['Attendance Average', f"{data.attendance_average}%"]
        ]
        
        overview_table = Table(overview_data, colWidths=[2.5*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue)
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Subject Performance in Section
        if data.subject_averages:
            story.append(Paragraph("Subject-wise Performance", styles['Heading2']))
            subject_data = [['Subject', 'Average Score', 'Performance Level']]
            for subject, avg in data.subject_averages.items():
                level = 'Excellent' if avg >= 90 else 'Good' if avg >= 75 else 'Average' if avg >= 60 else 'Needs Improvement'
                subject_data.append([subject, f"{avg}%", level])
            
            subject_table = Table(subject_data)
            subject_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow)
            ]))
            story.append(subject_table)
            story.append(Spacer(1, 20))
        
        # Top Performers
        if data.top_performers:
            story.append(Paragraph("Top Performers", styles['Heading2']))
            top_data = [['Rank', 'Student Name', 'Student ID', 'Average Score']]
            for i, student in enumerate(data.top_performers[:10], 1):
                top_data.append([str(i), student.full_name, student.student_id, f"{student.average_score}%"])
            
            top_table = Table(top_data)
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.gold),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(top_table)
    
    elif view_type == "subject" and subject_id:
        # SUBJECT ANALYSIS REPORT
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        title = f"Subject Analysis Report - {subject.name if subject else 'Unknown Subject'}"
        data = get_subject_performance(subject_id, db, educator.id)
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Subject Overview
        story.append(Paragraph("Subject Performance Analysis", styles['Heading2']))
        subject_overview = [
            ['Subject Details', 'Value'],
            ['Subject Name', data.subject_name],
            ['Subject Code', data.subject_code],
            ['Total Students', str(data.total_students)],
            ['Students Passed', str(data.passed_students)],
            ['Students Failed', str(data.failed_students)],
            ['Pass Rate', f"{data.pass_rate}%"],
            ['Average Score', f"{data.average_score}%"],
            ['Highest Score', f"{data.highest_score}%"],
            ['Lowest Score', f"{data.lowest_score}%"]
        ]
        
        subject_table = Table(subject_overview, colWidths=[2.5*inch, 2*inch])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.teal),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan)
        ]))
        story.append(subject_table)
        story.append(Spacer(1, 20))
        
        # Grade Distribution
        if data.grade_distribution:
            story.append(Paragraph("Grade Distribution", styles['Heading2']))
            grade_dist_data = [['Grade', 'Count', 'Percentage']]
            total_grades = sum(data.grade_distribution.values())
            for grade, count in data.grade_distribution.items():
                percentage = f"{(count/total_grades*100):.1f}%" if total_grades > 0 else "0%"
                grade_dist_data.append([grade, str(count), percentage])
            
            grade_dist_table = Table(grade_dist_data)
            grade_dist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.mistyrose)
            ]))
            story.append(grade_dist_table)
            story.append(Spacer(1, 20))
        
        # Section-wise Performance
        if data.sections_performance:
            story.append(Paragraph("Performance Across Sections", styles['Heading2']))
            section_perf_data = [['Section', 'Students', 'Average Score', 'Pass Rate']]
            for section_perf in data.sections_performance:
                section_perf_data.append([
                    section_perf['section_name'],
                    str(section_perf['total_students']),
                    f"{section_perf['average_score']}%",
                    f"{section_perf['pass_rate']}%"
                ])
            
            section_perf_table = Table(section_perf_data)
            section_perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.indigo),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender)
            ]))
            story.append(section_perf_table)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report parameters")
    
    # Add timestamp footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Save to temporary file
    import tempfile
    import os
    
    report_names = {
        "overall": "Overall_Performance_Report",
        "section": "Section_Analysis_Report", 
        "subject": "Subject_Analysis_Report"
    }
    filename = f"{report_names.get(view_type, 'Performance_Report')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Use system temporary directory
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )

async def generate_excel_report(view_type: str, section_id: Optional[int], subject_id: Optional[int], 
                              educator: Educator, db: Session) -> FileResponse:
    """Generate Excel performance report with different sheets based on view type"""
    
    # Create workbook with specific naming
    import tempfile
    import os
    
    report_names = {
        "overall": "Overall_Performance_Analysis",
        "section": "Section_Analysis_Report", 
        "subject": "Subject_Analysis_Report"
    }
    filename = f"{report_names.get(view_type, 'Performance_Report')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Use system temporary directory
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        
        if view_type == "overall":
            # OVERALL PERFORMANCE EXCEL REPORT
            data = await get_overall_performance(educator, db)
            
            # Executive Summary Sheet
            summary_df = pd.DataFrame([
                {'Metric': 'Total Sections', 'Value': data.total_sections, 'Status': '✓'},
                {'Metric': 'Total Students', 'Value': data.total_students, 'Status': '✓'},
                {'Metric': 'Total Subjects', 'Value': data.total_subjects, 'Status': '✓'},
                {'Metric': 'Overall Pass Rate (%)', 'Value': data.overall_pass_rate, 'Status': '✓' if data.overall_pass_rate >= 70 else '⚠'},
                {'Metric': 'Overall Average (%)', 'Value': data.overall_average, 'Status': '✓' if data.overall_average >= 75 else '⚠'},
                {'Metric': 'Report Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M'), 'Status': '✓'}
            ])
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # Grade Distribution Sheet
            if data.grade_level_stats:
                grade_dist_df = pd.DataFrame([
                    {
                        'Performance Level': 'Excellent (90%+)',
                        'Count': data.grade_level_stats.get('excellent', 0),
                        'Percentage': f"{(data.grade_level_stats.get('excellent', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"
                    },
                    {
                        'Performance Level': 'Good (75-89%)',
                        'Count': data.grade_level_stats.get('good', 0),
                        'Percentage': f"{(data.grade_level_stats.get('good', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"
                    },
                    {
                        'Performance Level': 'Average (60-74%)',
                        'Count': data.grade_level_stats.get('average', 0),
                        'Percentage': f"{(data.grade_level_stats.get('average', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"
                    },
                    {
                        'Performance Level': 'Below Average (<60%)',
                        'Count': data.grade_level_stats.get('below_average', 0),
                        'Percentage': f"{(data.grade_level_stats.get('below_average', 0)/data.total_students*100):.1f}%" if data.total_students > 0 else "0%"
                    }
                ])
                grade_dist_df.to_excel(writer, sheet_name='Grade Distribution', index=False)
            
            # Sections Comparison Sheet
            if data.sections_summary:
                sections_df = pd.DataFrame([
                    {
                        'Section Name': s.section_name,
                        'Total Students': s.total_students,
                        'Students Passed': s.passed_students,
                        'Students Failed': s.failed_students,
                        'Pass Rate (%)': s.pass_rate,
                        'Average Score (%)': s.average_score,
                        'Highest Score (%)': s.highest_score,
                        'Lowest Score (%)': s.lowest_score,
                        'Attendance Average (%)': s.attendance_average,
                        'Performance Rating': 'Excellent' if s.average_score >= 90 else 'Good' if s.average_score >= 75 else 'Average' if s.average_score >= 60 else 'Needs Improvement'
                    }
                    for s in data.sections_summary
                ])
                sections_df.to_excel(writer, sheet_name='Sections Comparison', index=False)
                
            # Subjects Analysis Sheet
            if data.subjects_summary:
                subjects_df = pd.DataFrame([
                    {
                        'Subject Name': subj.subject_name,
                        'Subject Code': subj.subject_code,
                        'Total Students': subj.total_students,
                        'Pass Rate (%)': subj.pass_rate,
                        'Average Score (%)': subj.average_score,
                        'Highest Score (%)': subj.highest_score,
                        'Lowest Score (%)': subj.lowest_score,
                        'Difficulty Level': 'Easy' if subj.pass_rate >= 90 else 'Moderate' if subj.pass_rate >= 70 else 'Challenging' if subj.pass_rate >= 50 else 'Very Challenging'
                    }
                    for subj in data.subjects_summary
                ])
                subjects_df.to_excel(writer, sheet_name='Subjects Analysis', index=False)
        
        elif view_type == "section" and section_id:
            # SECTION ANALYSIS EXCEL REPORT
            data = get_section_performance(section_id, db, educator.id)
            
            # Section Overview Sheet
            overview_df = pd.DataFrame([
                {'Detail': 'Section Name', 'Value': data.section_name},
                {'Detail': 'Total Students', 'Value': data.total_students},
                {'Detail': 'Students Passed', 'Value': data.passed_students},
                {'Detail': 'Students Failed', 'Value': data.failed_students},
                {'Detail': 'Pass Rate (%)', 'Value': data.pass_rate},
                {'Detail': 'Class Average (%)', 'Value': data.average_score},
                {'Detail': 'Highest Score (%)', 'Value': data.highest_score},
                {'Detail': 'Lowest Score (%)', 'Value': data.lowest_score},
                {'Detail': 'Attendance Average (%)', 'Value': data.attendance_average},
                {'Detail': 'Overall Rating', 'Value': 'Excellent' if data.average_score >= 85 else 'Good' if data.average_score >= 70 else 'Average' if data.average_score >= 60 else 'Needs Improvement'}
            ])
            overview_df.to_excel(writer, sheet_name='Section Overview', index=False)
            
            # Subject Performance in Section
            if data.subject_averages:
                subject_perf_df = pd.DataFrame([
                    {
                        'Subject': subject,
                        'Average Score (%)': avg,
                        'Performance Level': 'Excellent' if avg >= 90 else 'Good' if avg >= 75 else 'Average' if avg >= 60 else 'Needs Improvement',
                        'Grade': 'A+' if avg >= 95 else 'A' if avg >= 90 else 'B+' if avg >= 85 else 'B' if avg >= 80 else 'C+' if avg >= 75 else 'C' if avg >= 70 else 'D' if avg >= 60 else 'F'
                    }
                    for subject, avg in data.subject_averages.items()
                ])
                subject_perf_df.to_excel(writer, sheet_name='Subject Performance', index=False)
            
            # Top Performers Details
            if data.top_performers:
                top_performers_df = pd.DataFrame([
                    {
                        'Rank': i + 1,
                        'Student ID': student.student_id,
                        'Student Name': student.full_name,
                        'Email': student.email,
                        'Average Score (%)': student.average_score,
                        'Status': student.status,
                        'Total Subjects': student.total_subjects,
                        'Passed Subjects': student.passed_subjects,
                        'Failed Subjects': student.failed_subjects
                    }
                    for i, student in enumerate(data.top_performers)
                ])
                top_performers_df.to_excel(writer, sheet_name='Top Performers', index=False)
            
            # Students Needing Support
            if data.low_performers:
                low_performers_df = pd.DataFrame([
                    {
                        'Student ID': student.student_id,
                        'Student Name': student.full_name,
                        'Email': student.email,
                        'Average Score (%)': student.average_score,
                        'Status': student.status,
                        'Failed Subjects': student.failed_subjects,
                        'Subjects to Improve': student.total_subjects - student.passed_subjects,
                        'Attention Level': 'High' if student.average_score < 40 else 'Medium' if student.average_score < 55 else 'Low'
                    }
                    for student in data.low_performers
                ])
                low_performers_df.to_excel(writer, sheet_name='Students Needing Support', index=False)
        
        elif view_type == "subject" and subject_id:
            # SUBJECT ANALYSIS EXCEL REPORT
            data = get_subject_performance(subject_id, db, educator.id)
            
            # Subject Overview Sheet
            subject_overview_df = pd.DataFrame([
                {'Detail': 'Subject Name', 'Value': data.subject_name},
                {'Detail': 'Subject Code', 'Value': data.subject_code},
                {'Detail': 'Total Students', 'Value': data.total_students},
                {'Detail': 'Students Passed', 'Value': data.passed_students},
                {'Detail': 'Students Failed', 'Value': data.failed_students},
                {'Detail': 'Pass Rate (%)', 'Value': data.pass_rate},
                {'Detail': 'Average Score (%)', 'Value': data.average_score},
                {'Detail': 'Highest Score (%)', 'Value': data.highest_score},
                {'Detail': 'Lowest Score (%)', 'Value': data.lowest_score},
                {'Detail': 'Difficulty Assessment', 'Value': 'Easy' if data.pass_rate >= 90 else 'Moderate' if data.pass_rate >= 70 else 'Challenging' if data.pass_rate >= 50 else 'Very Challenging'}
            ])
            subject_overview_df.to_excel(writer, sheet_name='Subject Overview', index=False)
            
            # Grade Distribution Analysis
            if data.grade_distribution:
                grade_dist_df = pd.DataFrame([
                    {
                        'Grade': grade,
                        'Count': count,
                        'Percentage': f"{(count/data.total_students*100):.1f}%" if data.total_students > 0 else "0%",
                        'GPA Points': {'A+': 4.0, 'A': 4.0, 'B+': 3.5, 'B': 3.0, 'C+': 2.5, 'C': 2.0, 'D+': 1.5, 'D': 1.0, 'F': 0.0}.get(grade, 0.0)
                    }
                    for grade, count in data.grade_distribution.items()
                ])
                grade_dist_df.to_excel(writer, sheet_name='Grade Distribution', index=False)
            
            # Section-wise Performance Analysis
            if data.sections_performance:
                section_performance_df = pd.DataFrame([
                    {
                        'Section Name': section_perf['section_name'],
                        'Total Students': section_perf['total_students'],
                        'Passed Students': section_perf['passed_students'],
                        'Average Score (%)': section_perf['average_score'],
                        'Pass Rate (%)': section_perf['pass_rate'],
                        'Performance Level': 'Excellent' if section_perf['average_score'] >= 90 else 'Good' if section_perf['average_score'] >= 75 else 'Average' if section_perf['average_score'] >= 60 else 'Below Average',
                        'Recommendation': 'Continue current approach' if section_perf['pass_rate'] >= 80 else 'Review teaching methods' if section_perf['pass_rate'] >= 60 else 'Intensive support needed'
                    }
                    for section_perf in data.sections_performance
                ])
                section_performance_df.to_excel(writer, sheet_name='Sections Performance', index=False)
        
        # Add metadata sheet for all report types
        metadata_df = pd.DataFrame([
            {'Information': 'Report Type', 'Value': view_type.title() + ' Performance Analysis'},
            {'Information': 'Generated By', 'Value': f"{educator.first_name} {educator.last_name}"},
            {'Information': 'Generated On', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'Information': 'Academic Year', 'Value': '2024-2025'},
            {'Information': 'System', 'Value': 'Educator AI Assistant'},
            {'Information': 'Format Version', 'Value': '2.0'}
        ])
        metadata_df.to_excel(writer, sheet_name='Report Info', index=False)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Additional Download Endpoints for Frontend Compatibility
@router.get("/overview-download")
async def download_overview_report(
    format: Literal["pdf", "excel"] = Query("pdf"),
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Download overview performance report"""
    return await download_performance_report(format, "overall", None, None, current_educator, db)

@router.post("/filtered-download")
async def download_filtered_report(
    request: dict,
    format: Literal["pdf", "excel"] = Query("pdf"),
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Download filtered performance report"""
    # For now, return overall report - can be enhanced to handle filters
    return await download_performance_report(format, "overall", None, None, current_educator, db)

# ==================== REPORT SENDING FUNCTIONALITY ====================

class SendReportRequest(BaseModel):
    report_type: Literal["individual", "section", "subject"] = "individual"
    recipient_type: Literal["student", "parent", "both"] = "both"
    student_ids: Optional[List[int]] = None  # For individual reports
    section_id: Optional[int] = None  # For section reports
    subject_id: Optional[int] = None  # For subject reports
    title: str
    description: Optional[str] = None
    comments: Optional[str] = None
    format: Literal["pdf", "excel", "both"] = "pdf"

class SentReportResponse(BaseModel):
    id: int
    report_type: str
    title: str
    description: str
    recipient_type: str
    sent_at: datetime
    status: str
    is_viewed_by_student: bool
    is_viewed_by_parent: bool
    students_count: int
    format: str

@router.post("/send-report", response_model=Dict[str, Any])
async def send_performance_report(
    request: SendReportRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Send performance reports to students and/or parents"""
    
    try:
        sent_reports = []
        
        if request.report_type == "individual" and request.student_ids:
            # Send individual student reports
            for student_id in request.student_ids:
                student = db.query(Student).filter(Student.id == student_id).first()
                if not student:
                    continue
                
                # Generate and save the report
                report_file_path = await generate_and_save_student_report(
                    student, current_educator, db, request.format
                )
                
                # Get student performance data for storage
                report_data = get_student_performance_data(student, db)
                
                # Create sent report record
                sent_report = SentReport(
                    report_type=ReportType.INDIVIDUAL_STUDENT,
                    title=request.title,
                    description=request.description or f"Individual performance report for {student.full_name}",
                    educator_id=current_educator.id,
                    student_id=student.id,
                    recipient_type=RecipientType(request.recipient_type),
                    report_data=report_data,
                    report_file_path=report_file_path,
                    report_format=request.format,
                    comments=request.comments,
                    academic_year="2024-2025"
                )
                
                db.add(sent_report)
                sent_reports.append(sent_report)
        
        elif request.report_type == "section" and request.section_id:
            # Send section report to all students in section
            section = db.query(Section).filter(Section.id == request.section_id).first()
            if not section:
                raise HTTPException(status_code=404, detail="Section not found")
            
            # Generate section report
            report_file_path = await generate_and_save_section_report(
                section, current_educator, db, request.format
            )
            
            # Get section performance data
            report_data = get_section_performance(section.id, db, current_educator.id)
            
            # Send to all students in section
            students = db.query(Student).filter(Student.section_id == section.id).all()
            
            for student in students:
                sent_report = SentReport(
                    report_type=ReportType.SECTION_SUMMARY,
                    title=request.title,
                    description=request.description or f"Section performance report for {section.name}",
                    educator_id=current_educator.id,
                    student_id=student.id,
                    section_id=section.id,
                    recipient_type=RecipientType(request.recipient_type),
                    report_data=report_data.__dict__,
                    report_file_path=report_file_path,
                    report_format=request.format,
                    comments=request.comments,
                    academic_year="2024-2025"
                )
                
                db.add(sent_report)
                sent_reports.append(sent_report)
        
        elif request.report_type == "subject" and request.subject_id:
            # Send subject report to all students taking that subject
            subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
            if not subject:
                raise HTTPException(status_code=404, detail="Subject not found")
            
            # Generate subject report
            report_file_path = await generate_and_save_subject_report(
                subject, current_educator, db, request.format
            )
            
            # Get subject performance data
            report_data = get_subject_performance(subject.id, db, current_educator.id)
            
            # Send to all students taking this subject
            students = db.query(Student).join(Grade).filter(Grade.subject_id == subject.id).distinct().all()
            
            for student in students:
                sent_report = SentReport(
                    report_type=ReportType.SUBJECT_ANALYSIS,
                    title=request.title,
                    description=request.description or f"Subject performance report for {subject.name}",
                    educator_id=current_educator.id,
                    student_id=student.id,
                    subject_id=subject.id,
                    recipient_type=RecipientType(request.recipient_type),
                    report_data=report_data.__dict__,
                    report_file_path=report_file_path,
                    report_format=request.format,
                    comments=request.comments,
                    academic_year="2024-2025"
                )
                
                db.add(sent_report)
                sent_reports.append(sent_report)
        
        # Commit all changes
        db.commit()

        # Create notifications for each sent report so students see them in their dashboard
        try:
            for report in sent_reports:
                try:
                    notification = Notification(
                        educator_id=current_educator.id,
                        student_id=report.student_id,
                        title=f"Report: {report.title}",
                        message=report.description or report.title,
                        notification_type=NotificationType.GRADE_REPORT,
                        additional_data=str({"report_id": report.id})
                    )
                    db.add(notification)
                except Exception:
                    # Don't fail the whole operation for a single notification error
                    db.rollback()
            db.commit()
        except Exception:
            db.rollback()

        return {
            "success": True,
            "message": f"Successfully sent {len(sent_reports)} reports",
            "reports_sent": len(sent_reports),
            "report_ids": [report.id for report in sent_reports]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send reports: {str(e)}")

@router.get("/sent-reports", response_model=List[SentReportResponse])
async def get_sent_reports(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all reports sent by the current educator"""
    
    sent_reports = db.query(SentReport).filter(
        SentReport.educator_id == current_educator.id
    ).order_by(SentReport.sent_at.desc()).all()
    
    result = []
    for report in sent_reports:
        # Count students who received this report
        if report.report_type == ReportType.INDIVIDUAL_STUDENT:
            students_count = 1
        elif report.section_id:
            students_count = db.query(Student).filter(Student.section_id == report.section_id).count()
        else:
            students_count = db.query(SentReport).filter(
                SentReport.educator_id == current_educator.id,
                SentReport.title == report.title,
                SentReport.sent_at == report.sent_at
            ).count()
        
        result.append(SentReportResponse(
            id=report.id,
            report_type=report.report_type.value,
            title=report.title,
            description=report.description or "",
            recipient_type=report.recipient_type.value,
            sent_at=report.sent_at,
            status=report.status.value,
            is_viewed_by_student=report.is_viewed_by_student,
            is_viewed_by_parent=report.is_viewed_by_parent,
            students_count=students_count,
            format=report.report_format
        ))
    
    return result

# Helper functions for generating and saving reports

async def generate_and_save_student_report(student: Student, educator: Educator, db: Session, format: str) -> str:
    """Generate and save individual student report"""
    import tempfile
    import os
    
    # Generate report based on format
    if format == "pdf" or format == "both":
        # Generate PDF report for individual student
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph(f"Individual Performance Report - {student.full_name}", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Student information
        student_info = [
            ['Student Name', student.full_name],
            ['Student ID', student.student_id],
            ['Section', student.section.name if student.section else 'N/A'],
            ['Report Date', datetime.now().strftime('%Y-%m-%d')],
            ['Generated by', f"{educator.first_name} {educator.last_name}"]
        ]
        
        info_table = Table(student_info, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Performance data
        grades = db.query(Grade).filter(Grade.student_id == student.id).all()
        if grades:
            story.append(Paragraph("Academic Performance", styles['Heading2']))
            
            performance_data = [['Subject', 'Marks', 'Percentage', 'Grade', 'Status']]
            for grade in grades:
                performance_data.append([
                    grade.subject.name if grade.subject else 'Unknown',
                    f"{grade.marks_obtained}/{grade.total_marks}",
                    f"{grade.percentage:.1f}%",
                    grade.grade_letter or 'N/A',
                    'Pass' if grade.is_passed else 'Fail'
                ])
            
            perf_table = Table(performance_data)
            perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(perf_table)
        
        doc.build(story)
        buffer.seek(0)
        
        # Save to file
        temp_dir = tempfile.gettempdir()
        filename = f"student_report_{student.student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(buffer.getvalue())
        
        return filepath
    
    return ""

async def generate_and_save_section_report(section: Section, educator: Educator, db: Session, format: str) -> str:
    """Generate and save section report"""
    import tempfile
    import os
    
    if format == "pdf" or format == "both":
        # Use existing section report generation logic
        return await generate_pdf_report("section", section.id, None, educator, db)
    
    return ""

async def generate_and_save_subject_report(subject: Subject, educator: Educator, db: Session, format: str) -> str:
    """Generate and save subject report"""
    import tempfile
    import os
    
    if format == "pdf" or format == "both":
        # Use existing subject report generation logic
        return await generate_pdf_report("subject", None, subject.id, educator, db)
    
    return ""

def get_student_performance_data(student: Student, db: Session) -> Dict:
    """Get student performance data for JSON storage"""
    grades = db.query(Grade).filter(Grade.student_id == student.id).all()
    
    performance_data = {
        "student_id": student.id,
        "student_name": student.full_name,
        "section": student.section.name if student.section else None,
        "subjects": [],
        "overall_average": 0,
        "total_subjects": len(grades),
        "passed_subjects": 0
    }
    
    if grades:
        total_percentage = 0
        passed_count = 0
        
        for grade in grades:
            subject_data = {
                "subject_name": grade.subject.name if grade.subject else 'Unknown',
                "marks_obtained": grade.marks_obtained,
                "total_marks": grade.total_marks,
                "percentage": grade.percentage,
                "grade_letter": grade.grade_letter,
                "is_passed": grade.is_passed
            }
            performance_data["subjects"].append(subject_data)
            
            if grade.percentage:
                total_percentage += grade.percentage
                
            if grade.is_passed:
                passed_count += 1
        
        performance_data["overall_average"] = total_percentage / len(grades) if grades else 0
        performance_data["passed_subjects"] = passed_count
    
    return performance_data

# Real-time WebSocket endpoint for live performance updates
@router.websocket("/ws/performance/{educator_id}")
async def websocket_performance_updates(
    websocket: WebSocket, 
    educator_id: int
):
    """WebSocket endpoint for real-time performance updates"""
    try:
        await websocket.accept()
        print(f"WebSocket connected for educator {educator_id}")
        
        while True:
            # Get database session
            db = next(get_db())
            
            try:
                # Get educator
                educator = db.query(Educator).filter(Educator.id == educator_id).first()
                if not educator:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Educator not found"
                    }))
                    break
                
                # Get updated performance data
                performance_data = await get_overall_performance(current_educator=educator, db=db)
                
                update_message = {
                    "type": "performance_update",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "total_students": performance_data.total_students,
                        "overall_average": performance_data.overall_average,
                        "overall_pass_rate": performance_data.overall_pass_rate,
                        "grade_distribution": performance_data.grade_distribution,
                        "subject_performance_chart": performance_data.subject_performance_chart,
                        "sections_performance_chart": performance_data.sections_performance_chart,
                        "attendance_stats": performance_data.attendance_stats,
                        "top_performers_count": len(performance_data.top_performers),
                        "low_performers_count": len(performance_data.low_performers)
                    }
                }
                
                await websocket.send_text(json.dumps(update_message))
                print(f"Sent performance update to educator {educator_id}")
                
            except Exception as e:
                print(f"Error in performance update: {e}")
            finally:
                db.close()
            
            # Wait 10 seconds before next update (reduced from 30 for more real-time feel)
            await asyncio.sleep(10)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for educator {educator_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")

# Connection Manager for WebSocket connections
class PerformanceConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # educator_id -> [websockets]

    async def connect(self, websocket: WebSocket, educator_id: int):
        if educator_id not in self.active_connections:
            self.active_connections[educator_id] = []
        self.active_connections[educator_id].append(websocket)

    def disconnect(self, websocket: WebSocket, educator_id: int):
        if educator_id in self.active_connections:
            self.active_connections[educator_id].remove(websocket)
            if not self.active_connections[educator_id]:
                del self.active_connections[educator_id]

    async def send_update_to_educator(self, educator_id: int, update_data: dict):
        """Send real-time update to all connected clients for an educator"""
        if educator_id in self.active_connections:
            disconnected_connections = []
            for websocket in self.active_connections[educator_id]:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except:
                    disconnected_connections.append(websocket)
            
            # Remove disconnected connections
            for ws in disconnected_connections:
                self.active_connections[educator_id].remove(ws)

performance_manager = PerformanceConnectionManager()

# Event-driven real-time update functions
async def notify_grade_update(grade: Grade, db: Session):
    """Notify when a grade is added or updated"""
    try:
        # Find the educator for this grade
        student = db.query(Student).filter(Student.id == grade.student_id).first()
        if not student:
            return
            
        section = db.query(Section).filter(Section.id == student.section_id).first()
        if not section:
            return
            
        # Get updated performance data
        educator = db.query(Educator).filter(Educator.id == section.educator_id).first()
        if not educator:
            return
            
        performance_data = await get_overall_performance(current_educator=educator, db=db)
        
        update_message = {
            "type": "grade_update",
            "event": "grade_updated",
            "timestamp": datetime.now().isoformat(),
            "grade_data": {
                "student_name": student.name,
                "subject_name": grade.subject.name if grade.subject else "Unknown",
                "score": grade.marks_obtained,
                "total_marks": grade.total_marks
            },
            "performance_data": {
                "total_students": performance_data.total_students,
                "overall_average": performance_data.overall_average,
                "overall_pass_rate": performance_data.overall_pass_rate,
                "grade_distribution": performance_data.grade_distribution,
                "subject_performance_chart": performance_data.subject_performance_chart,
                "sections_performance_chart": performance_data.sections_performance_chart
            }
        }
        
        await performance_manager.send_update_to_educator(educator.id, update_message)
        print(f"Sent grade update notification to educator {educator.id}")
        
    except Exception as e:
        print(f"Error in grade update notification: {e}")

async def notify_attendance_update(attendance: Attendance, db: Session):
    """Notify when attendance is updated"""
    try:
        # Find the educator for this attendance record
        student = db.query(Student).filter(Student.id == attendance.student_id).first()
        if not student:
            return
            
        section = db.query(Section).filter(Section.id == student.section_id).first()
        if not section:
            return
            
        educator = db.query(Educator).filter(Educator.id == section.educator_id).first()
        if not educator:
            return
            
        # Calculate attendance stats
        total_records = db.query(Attendance).filter(Attendance.student_id == student.id).count()
        present_records = db.query(Attendance).filter(
            Attendance.student_id == student.id,
            Attendance.status == 'present'
        ).count()
        
        attendance_percentage = (present_records / total_records * 100) if total_records > 0 else 0
        
        update_message = {
            "type": "attendance_update", 
            "event": "attendance_updated",
            "timestamp": datetime.now().isoformat(),
            "attendance_data": {
                "student_name": student.name,
                "date": attendance.date.isoformat(),
                "status": attendance.status,
                "attendance_percentage": round(attendance_percentage, 1)
            }
        }
        
        await performance_manager.send_update_to_educator(educator.id, update_message)
        print(f"Sent attendance update notification to educator {educator.id}")
        
    except Exception as e:
        print(f"Error in attendance update notification: {e}")

async def notify_exam_created(exam: Exam, db: Session):
    """Notify when a new exam is created"""
    try:
        # Find the educator for this exam
        section = db.query(Section).filter(Section.id == exam.section_id).first()
        if not section:
            return
            
        educator = db.query(Educator).filter(Educator.id == section.educator_id).first()
        if not educator:
            return
            
        update_message = {
            "type": "exam_created",
            "event": "exam_created", 
            "timestamp": datetime.now().isoformat(),
            "exam_data": {
                "exam_name": exam.name,
                "subject_name": exam.subject.name if exam.subject else "Unknown",
                "exam_date": exam.exam_date.isoformat() if exam.exam_date else None,
                "total_marks": exam.total_marks,
                "section_name": section.name
            }
        }
        
        await performance_manager.send_update_to_educator(educator.id, update_message)
        print(f"Sent exam created notification to educator {educator.id}")
        
    except Exception as e:
        print(f"Error in exam created notification: {e}")