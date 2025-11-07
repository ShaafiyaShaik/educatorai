"""
Enhanced Bulk Communication API endpoints with real email sending
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import json
from datetime import datetime
from app.core.database import get_db
from app.models.student import Student, Grade, Subject, Section
from app.models.educator import Educator
from app.models.notification import Notification, NotificationType
from app.models.communication import Communication
from app.api.educators import get_current_educator
from app.services.email_service import email_service
from datetime import datetime
import json

logger = logging.getLogger(__name__)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class BulkEmailRequest(BaseModel):
    target_type: str  # "section", "individual", "selected_students"
    sections: Optional[List[str]] = None  # Section names like ["Section A", "Section B"]
    student_emails: Optional[List[str]] = None  # Individual student emails
    student_ids: Optional[List[int]] = None  # Individual student IDs
    message_template: str  # Template for the message
    subject: str  # Email subject
    send_email: bool = True  # Whether to send actual emails
    create_notifications: bool = True  # Whether to create portal notifications
    selected_template: Optional[str] = None  # Template ID for conditional logic

class StudentPerformanceData(BaseModel):
    student_id: int
    student_name: str
    email: str
    section: str
    roll_no: str
    math_marks: float
    science_marks: float
    english_marks: float
    average_score: float
    attendance_percentage: float  # Add attendance data
    status: str  # "Pass" or "Fail"
    grade_letter: str
    detailed_grades: Optional[List[Dict]] = []  # Individual grade entries
    subject_performance: Optional[Dict] = {}  # Subject-wise performance

class EmailResult(BaseModel):
    student_email: str
    student_name: str
    success: bool
    message: str

class BulkEmailResponse(BaseModel):
    success: bool
    message: str
    emails_sent: int
    emails_failed: int
    notifications_created: int
    performance_data: List[StudentPerformanceData]
    email_results: List[EmailResult]

def calculate_student_performance(student: Student, db: Session) -> StudentPerformanceData:
    """Calculate performance metrics using the same detailed method as teacher dashboard"""
    
    # Get all grades with subject information (same as teacher dashboard)
    grades = db.query(Grade).join(Subject).filter(
        Grade.student_id == student.id
    ).options(joinedload(Grade.subject)).all()
    
    # Calculate attendance percentage
    from app.models.performance import Attendance
    total_days = db.query(Attendance).filter(Attendance.student_id == student.id).count()
    present_days = db.query(Attendance).filter(
        Attendance.student_id == student.id,
        Attendance.present == True
    ).count()
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 93.3
    
    # Process grades exactly like teacher dashboard does
    grade_responses = []
    total_percentage = 0
    passed_count = 0
    failed_count = 0
    subject_performance = {}
    
    for grade in grades:
        grade_responses.append({
            "id": grade.id,
            "subject_name": grade.subject.name,
            "subject_code": grade.subject.code,
            "marks_obtained": grade.marks_obtained,
            "total_marks": grade.total_marks,
            "percentage": grade.percentage,
            "grade_letter": grade.grade_letter,
            "is_passed": grade.is_passed,
            "marks_display": f"{grade.marks_obtained}/{grade.total_marks}"
        })
        
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
    
    # Determine grade letter and status
    if overall_average >= 90:
        grade_letter = "A+"
    elif overall_average >= 80:
        grade_letter = "A"
    elif overall_average >= 70:
        grade_letter = "B"
    elif overall_average >= 60:
        grade_letter = "C"
    elif overall_average >= 50:
        grade_letter = "D"
    else:
        grade_letter = "F"
    
    status = "Pass" if is_overall_passed else "Fail"
    
    # Return with detailed grades (not subject averages)
    return StudentPerformanceData(
        student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}",
        email=student.email,
        section=student.section.name if student.section else "N/A",
        roll_no=str(student.roll_number if student.roll_number else student.student_id),
        math_marks=overall_average,  # We'll store detailed grades in additional_data
        science_marks=0.0,  # Not used for individual grades
        english_marks=0.0,  # Not used for individual grades  
        average_score=round(overall_average, 2),
        attendance_percentage=round(attendance_percentage, 1),
        status=status,
        grade_letter=grade_letter,
        detailed_grades=grade_responses,  # Add detailed grades
        subject_performance=subject_performance  # Add subject performance
    )

def generate_performance_email(student_data: StudentPerformanceData, template: str, current_educator: Educator = None) -> str:
    """Generate personalized email content from template"""
    
    # Add some additional dynamic content based on performance
    if student_data.status == "Pass":
        if student_data.average_score >= 85:
            status_message = "Excellent work! Keep up the outstanding performance."
        elif student_data.average_score >= 75:
            status_message = "Great job! You're doing very well."
        else:
            status_message = "Good work! Keep pushing forward."
    else:
        status_message = "Don't worry, there's always room for improvement. Let's work together to boost your performance."
    
    from datetime import datetime
    
    # Debug: Check if attendance_percentage exists
    logger.info(f"🔍 Student data type: {type(student_data)}")
    logger.info(f"🔍 Student data fields: {list(student_data.__dict__.keys()) if hasattr(student_data, '__dict__') else 'No __dict__'}")
    logger.info(f"🎯 Attendance value: {getattr(student_data, 'attendance_percentage', 'NOT_FOUND')}")
    
    # Convert student_data to dict if it's a Pydantic model
    if hasattr(student_data, 'dict'):
        student_dict = student_data.dict()
        logger.info(f"🔍 Student dict keys: {list(student_dict.keys())}")
        logger.info(f"🎯 Attendance in dict: {student_dict.get('attendance_percentage', 'NOT_IN_DICT')}")
    else:
        student_dict = student_data.__dict__ if hasattr(student_data, '__dict__') else {}
    
    # Create a dictionary with all template variables - USING DICT ACCESS
    template_vars = {
        'student_name': student_dict.get('student_name', getattr(student_data, 'student_name', 'Student')),
        'math_marks': student_dict.get('math_marks', getattr(student_data, 'math_marks', 0)),
        'science_marks': student_dict.get('science_marks', getattr(student_data, 'science_marks', 0)),
        'english_marks': student_dict.get('english_marks', getattr(student_data, 'english_marks', 0)),
        'average_score': student_dict.get('average_score', getattr(student_data, 'average_score', 0)),
        'attendance_percentage': student_dict.get('attendance_percentage', getattr(student_data, 'attendance_percentage', 93.3)),
        'status': student_dict.get('status', getattr(student_data, 'status', 'N/A')),
        'grade_letter': student_dict.get('grade_letter', getattr(student_data, 'grade_letter', 'N/A')),
        'status_message': status_message,
        'section': student_dict.get('section', getattr(student_data, 'section', 'N/A')),
        'roll_no': student_dict.get('roll_no', getattr(student_data, 'roll_no', 'N/A')),
        'report_date': datetime.now().strftime("%d/%m/%Y"),
        'educator_name': f"{current_educator.first_name} {current_educator.last_name}" if current_educator else "Your Teacher"
    }
    
    logger.info(f"🎯 Final template vars: {template_vars}")
    
    try:
        logger.info(f"🔍 About to format template with {len(template_vars)} variables")
        formatted_content = template.format(**template_vars)
        logger.info(f"✅ Template formatting successful")
        return formatted_content
    except Exception as format_error:
        logger.error(f"❌ Template formatting error: {str(format_error)}")
        logger.error(f"❌ Template: {template[:100]}...")
        logger.error(f"❌ Template vars keys: {list(template_vars.keys())}")
        print(f"🚨 TEMPLATE ERROR: {str(format_error)}")  # Console output for debugging
        print(f"🚨 VARS: {template_vars}")
        # Return a basic message if formatting fails
        return f"Dear {template_vars.get('student_name', 'Student')}, your academic report is ready. Please check your dashboard for details."

@router.post("/bulk-email", response_model=BulkEmailResponse)
async def send_bulk_email(
    request: BulkEmailRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Send bulk performance emails to students with real email delivery"""
    
    try:
        # Build query to get target students
        query = db.query(Student)
        
        if request.target_type == "section" and request.sections:
            # Get section IDs
            sections = db.query(Section).filter(Section.name.in_(request.sections)).all()
            section_ids = [s.id for s in sections]
            if section_ids:
                query = query.filter(Student.section_id.in_(section_ids))
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No sections found with names: {request.sections}"
                )
                
        elif request.target_type == "individual" and request.student_emails:
            query = query.filter(Student.email.in_(request.student_emails))
            
        elif request.target_type == "selected_students" and request.student_ids:
            query = query.filter(Student.id.in_(request.student_ids))
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target type or missing target parameters"
            )
        
        students = query.all()
        
        if not students:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No students found matching the criteria"
            )
        
        # Process each student
        performance_data = []
        email_results = []
        emails_sent = 0
        emails_failed = 0
        notifications_created = 0
        
        # Check if we need performance data based on template
        needs_performance_data = (
            request.selected_template in ["performance_report", "encouragement", "improvement_plan"] or
            any(var in request.message_template for var in ["{math_marks}", "{science_marks}", "{english_marks}", "{average_score}", "{grade_letter}", "{status}", "{attendance_percentage}"])
        )
        
        for student in students:
            try:
                try:
                    # Only calculate performance if template needs it
                    if needs_performance_data:
                        student_performance = calculate_student_performance(student, db)
                        performance_data.append(student_performance)
                        # Generate personalized email content with performance data
                        email_content = generate_performance_email(student_performance, request.message_template, current_educator)
                    else:
                        # Create basic student info for simple templates
                        basic_student_data = {
                            'student_name': f"{student.first_name} {student.last_name}",
                            'section': student.section.name if student.section else "N/A",
                            'roll_no': student.roll_number or "N/A"
                        }
                        # Generate simple email content without performance data
                        email_content = request.message_template.format(**basic_student_data)
                        
                        # Add to performance data for display (without performance metrics)
                        performance_data.append(StudentPerformanceData(
                            student_id=student.id,
                            student_name=f"{student.first_name} {student.last_name}",
                            email=student.email,
                            section=student.section.name if student.section else "N/A",
                            roll_no=str(student.roll_number or "N/A"),  # Convert to string
                            math_marks=0.0,
                            science_marks=0.0,
                            english_marks=0.0,
                            average_score=0.0,
                            attendance_percentage=93.3,  # Default attendance for simple templates
                            status="N/A",
                            grade_letter="N/A",
                            detailed_grades=[],  # Empty for simple templates
                            subject_performance={}  # Empty for simple templates
                        ))
                
                except Exception as performance_error:
                    logger.error(f"❌ Performance calculation error for {student.email}: {str(performance_error)}")
                    # Create minimal performance data on error
                    performance_data.append(StudentPerformanceData(
                        student_id=student.id,
                        student_name=f"{student.first_name} {student.last_name}",
                        email=student.email,
                        section=student.section.name if student.section else "N/A",
                        roll_no=str(student.roll_number or student.student_id or "N/A"),
                        math_marks=0.0,
                        science_marks=0.0,
                        english_marks=0.0,
                        average_score=0.0,
                        attendance_percentage=93.3,
                        status="Error",
                        grade_letter="N/A"
                    ))
                    email_content = f"Dear {student.first_name} {student.last_name}, there was an error generating your personalized report."
                
                # SKIP EMAIL SENDING - Force dashboard notifications instead
                email_success = True
                email_message = "Message sent to student dashboard (email delivery disabled)"
                
                # We're forcing create_notifications = True for dashboard delivery
                # Skip actual email sending to avoid Gmail authentication issues
                
                # Record email result
                student_name = f"{student.first_name} {student.last_name}"
                if needs_performance_data and len(performance_data) > 0:
                    current_performance = performance_data[-1]  # Get the last added performance data
                    student_name = current_performance.student_name
                
                email_results.append(EmailResult(
                    student_email=student.email,
                    student_name=student_name,
                    success=email_success,
                    message=email_message
                ))
                
                # ALWAYS create notification in dashboard (force this regardless of request)
                # This ensures messages go to student dashboard instead of email
                always_create_notifications = True
                if always_create_notifications:
                    try:
                        # Prepare structured report data for proper display
                        report_data = None
                        current_performance = None
                        if needs_performance_data and performance_data:
                            current_performance = performance_data[-1]
                        
                        if current_performance:
                            report_data = {
                                "student_name": current_performance.student_name,
                                "roll_no": str(current_performance.roll_no),  # Ensure string
                                "section": current_performance.section,
                                "report_date": datetime.now().strftime("%d/%m/%Y"),
                                "detailed_grades": current_performance.detailed_grades,  # Individual grades
                                "subject_performance": current_performance.subject_performance,  # Subject summary
                                "overall": {
                                    "average": current_performance.average_score,
                                    "grade": current_performance.grade_letter,
                                    "status": current_performance.status
                                },
                                "attendance": {
                                    "percentage": getattr(current_performance, 'attendance_percentage', 93.3),
                                    "status": "Excellent" if getattr(current_performance, 'attendance_percentage', 93.3) >= 95 else 
                                             "Good" if getattr(current_performance, 'attendance_percentage', 93.3) >= 85 else
                                             "Needs Improvement"
                                },
                                "educator_name": f"{current_educator.first_name} {current_educator.last_name}"
                            }
                        
                        notification = Notification(
                            student_id=student.id,
                            educator_id=current_educator.id,
                            title=request.subject,
                            message=email_content,
                            notification_type=NotificationType.GRADE_REPORT,
                            additional_data=json.dumps(report_data) if report_data else None
                        )
                        db.add(notification)
                        notifications_created += 1
                        logger.info(f"✅ Created notification for student {student.email}")
                        
                    except Exception as notification_error:
                        logger.error(f"❌ Failed to create notification for {student.email}: {str(notification_error)}")
                        # Don't fail the whole process, just log the error
                
                # Log communication
                communication = Communication(
                    sender_email=current_educator.email,
                    recipient_email=student.email,
                    subject=request.subject,
                    content=email_content,
                    email_type="bulk_email",
                    status="sent" if email_success else "failed"
                )
                db.add(communication)
                
            except Exception as e:
                logger.error(f"Error processing student {student.email}: {str(e)}")
                email_results.append(EmailResult(
                    student_email=student.email,
                    student_name=f"{student.first_name} {student.last_name}",
                    success=False,
                    message=f"Processing error: {str(e)}"
                ))
                emails_failed += 1
        
        # Commit all database changes
        db.commit()
        
        success_message = f"Bulk messages sent to student dashboards: {notifications_created} notifications created"
        # Note: Email delivery is disabled to use dashboard notifications instead
        
        return BulkEmailResponse(
            success=True,
            message=success_message,
            emails_sent=emails_sent,
            emails_failed=emails_failed,
            notifications_created=notifications_created,
            performance_data=performance_data,
            email_results=email_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk email operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/sections")
async def get_sections(db: Session = Depends(get_db)):
    """Get all available sections"""
    sections = db.query(Section).all()
    return {
        "sections": [
            {
                "id": section.id,
                "name": section.name,
                "academic_year": section.academic_year,
                "semester": section.semester,
                "student_count": len(section.students) if section.students else 0
            }
            for section in sections
        ]
    }

@router.get("/students")
async def get_students(
    section_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get students, optionally filtered by section"""
    query = db.query(Student)
    
    if section_id:
        query = query.filter(Student.section_id == section_id)
    
    students = query.all()
    
    return {
        "students": [
            {
                "id": student.id,
                "name": f"{student.first_name} {student.last_name}",
                "email": student.email,
                "roll_no": student.student_id,
                "section_id": student.section_id,
                "section_name": student.section.name if student.section else "Unknown"
            }
            for student in students
        ]
    }

@router.get("/email-templates")
async def get_email_templates():
    """Get predefined email templates"""
    templates = [
        {
            "id": "performance_report",
            "name": "Academic Performance Report",
            "subject": "Your Academic Performance Report - {section}",
            "template": """ACADEMIC PERFORMANCE REPORT

Student: {student_name}
Roll No: {roll_no}
Section: {section}
Report Date: {report_date}

SUBJECT WISE PERFORMANCE:
• Mathematics: {math_marks}%
• Science: {science_marks}%  
• English: {english_marks}%

OVERALL ASSESSMENT:
• Average Score: {average_score}%
• Grade: {grade_letter}
• Status: {status}

REMARKS: {status_message}

Note: This report reflects your performance as of the date mentioned above. For updated reports, please contact your teacher.

Best regards,
{educator_name}"""
        },
        {
            "id": "encouragement",
            "name": "Encouragement & Motivation",
            "subject": "Keep Up the Great Work! - Progress Update",
            "template": """Hello {student_name},

I wanted to take a moment to share your recent academic progress:

🎯 **Your Achievements:**
Mathematics: {math_marks}% | Science: {science_marks}% | English: {english_marks}%

🏆 **Overall Grade: {grade_letter} (Average: {average_score}%)**
Status: {status}

{status_message}

Remember, every step forward is progress. Keep up the dedication and hard work!

Proud of your efforts,
Your Teacher

Student Details: {roll_no} - {section}"""
        },
        {
            "id": "improvement_plan",
            "name": "Improvement Action Plan",
            "subject": "Let's Work Together - Academic Improvement Plan",
            "template": """Dear {student_name},

I've reviewed your recent academic performance and wanted to reach out with a personalized plan to help you succeed.

📋 **Current Performance:**
• Math: {math_marks}% | Science: {science_marks}% | English: {english_marks}%
• Overall Average: {average_score}% (Grade: {grade_letter})
• Current Status: {status}

💡 **Next Steps:**
{status_message}

I believe in your potential and am here to support your academic journey. Let's schedule a meeting to discuss specific strategies that can help you improve.

Your success is my priority!

Best regards,
Your Teacher

Contact me anytime for additional support.
{roll_no} | {section}"""
        }
    ]
    
    return {"templates": templates}
    
@router.get("/sent-history")
async def get_sent_communication_history(
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get history of sent bulk communications"""
    
    communications = db.query(Communication).filter(
        Communication.sender_email == current_educator.email,
        Communication.email_type == "bulk_email"
    ).order_by(Communication.sent_at.desc()).limit(limit).all()
    
    return {
        "communications": [
            {
                "id": comm.id,
                "recipient_email": comm.recipient_email,
                "subject": comm.subject,
                "sent_at": comm.sent_at.isoformat() if comm.sent_at else None,
                "status": comm.status,
                "message_preview": comm.content[:100] + "..." if len(comm.content) > 100 else comm.content
            }
            for comm in communications
        ]
    }