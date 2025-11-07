"""
Student dashboard API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from pydantic import BaseModel
from typing import List, Optional, Literal
from app.core.database import get_db
import os
import json
from datetime import datetime, timezone, timedelta
from app.models.student import Student, Grade, Subject
from app.models.schedule import Schedule, EventType
from app.models.communication import Communication
from app.models.notification import Notification, NotificationStatus
from app.models.report import SentReport, ReportStatus, RecipientType as ReportRecipientType
from app.models.meeting_schedule import Meeting, MeetingRecipient, RecipientType
from app.models import Educator
from app.api.students_auth import get_current_student
from datetime import datetime, date, timedelta

router = APIRouter()

# Timezone conversion function (assuming local timezone is UTC+5:30 for India)
def convert_to_local_time(utc_time):
    """Convert UTC time to local timezone (IST)"""
    if utc_time is None:
        return datetime.now()
    
    # Add timezone info if missing
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    
    # Convert to IST (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = utc_time + ist_offset
    
    return ist_time.replace(tzinfo=None)  # Remove timezone info for display

# Pydantic models
class SubjectGrade(BaseModel):
    subject_name: str
    subject_code: str
    marks_obtained: float
    total_marks: float
    percentage: float
    grade_letter: str
    is_passed: bool

class StudentMarks(BaseModel):
    grades: List[SubjectGrade]
    overall_average: float
    total_subjects: int
    passed_subjects: int
    failed_subjects: int
    overall_status: str  # "Pass" or "Fail"

class StudentNotification(BaseModel):
    id: int
    title: str
    message: str
    from_educator: str
    sent_at: datetime
    is_read: bool
    message_type: str
    report_data: Optional[dict] = None  # Structured report data


class StudentMessageItem(BaseModel):
    id: int
    subject: str
    message: str
    from_educator: str
    sent_at: datetime
    is_read: bool
    receiver_type: str

    class Config:
        from_attributes = True

class ScheduledEvent(BaseModel):
    id: int
    title: str
    description: str
    event_type: str  # "task" or "meeting"
    start_datetime: datetime
    end_datetime: datetime
    location: str
    educator_name: str
    status: str
    # Meeting-specific fields
    virtual_meeting_link: Optional[str] = None
    duration_minutes: Optional[int] = None
    requires_rsvp: Optional[bool] = None
    rsvp_status: Optional[str] = None

class ContactTeacherMessage(BaseModel):
    subject: str
    message: str
    recipient_educator_id: int

class ReceivedReport(BaseModel):
    id: int
    report_type: str
    title: str
    description: str
    from_educator: str
    sent_at: datetime
    is_viewed_by_student: bool
    is_viewed_by_parent: bool
    recipient_type: str
    report_format: str
    comments: Optional[str]
    academic_year: str
    download_url: Optional[str] = None
    
class ParentModeReport(BaseModel):
    id: int
    report_type: str
    title: str
    description: str
    from_educator: str
    sent_at: datetime
    is_viewed_by_parent: bool
    recipient_type: str
    report_format: str
    comments: Optional[str]
    academic_year: str
    student_name: str
    download_url: Optional[str] = None

# Endpoints
@router.get("/marks", response_model=StudentMarks)
async def get_student_marks(current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    """Get student's marks and grades"""
    
    # Get all grades for the student with subject information
    grades = db.query(Grade).join(Subject).filter(
        Grade.student_id == current_student.id
    ).all()
    
    if not grades:
        return StudentMarks(
            grades=[],
            overall_average=0.0,
            total_subjects=0,
            passed_subjects=0,
            failed_subjects=0,
            overall_status="No Grades"
        )
    
    # Process grades
    subject_grades = []
    total_percentage = 0
    passed_count = 0
    
    for grade in grades:
        # Calculate percentage if not already calculated
        if grade.percentage is None:
            grade.calculate_percentage()
        
        # Calculate grade letter if not already calculated
        if grade.grade_letter is None:
            grade.calculate_grade_letter()
        
        subject_grade = SubjectGrade(
            subject_name=grade.subject.name,
            subject_code=grade.subject.code,
            marks_obtained=grade.marks_obtained,
            total_marks=grade.total_marks,
            percentage=grade.percentage,
            grade_letter=grade.grade_letter,
            is_passed=grade.is_passed
        )
        subject_grades.append(subject_grade)
        total_percentage += grade.percentage
        
        if grade.is_passed:
            passed_count += 1
    
    # Calculate overall metrics
    total_subjects = len(grades)
    overall_average = total_percentage / total_subjects if total_subjects > 0 else 0
    failed_subjects = total_subjects - passed_count
    overall_status = "Pass" if passed_count == total_subjects else "Fail"
    
    return StudentMarks(
        grades=subject_grades,
        overall_average=round(overall_average, 2),
        total_subjects=total_subjects,
        passed_subjects=passed_count,
        failed_subjects=failed_subjects,
        overall_status=overall_status
    )

@router.get("/notifications", response_model=List[StudentNotification])
async def get_student_notifications(current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    """Get notifications for the student"""
    
    student_notifications = []
    
    # Get notifications from the Notification model (new bulk communication system)
    portal_notifications = db.query(Notification).filter(
        Notification.student_id == current_student.id
    ).order_by(Notification.created_at.desc()).all()
    
    for notification in portal_notifications:
        # Parse report data if available
        report_data = None
        if notification.additional_data:
            try:
                report_data = json.loads(notification.additional_data)
            except:
                report_data = None
        
        student_notification = StudentNotification(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            from_educator=notification.educator.full_name if notification.educator else "System",
            sent_at=convert_to_local_time(notification.created_at),
            is_read=(notification.status == NotificationStatus.READ),
            message_type=notification.notification_type.value if notification.notification_type else "info",
            report_data=report_data
        )
        student_notifications.append(student_notification)
    
    # Note: Removed old Communication model fetching to avoid duplicates
    # All notifications now come through the Notification model from bulk communication
    
    # Sort all notifications by sent_at descending
    student_notifications.sort(key=lambda x: x.sent_at, reverse=True)
    
    return student_notifications


@router.get("/messages", response_model=List[StudentMessageItem])
async def get_student_messages(
    view: Literal["student", "parent"] = "student",
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get educator messages sent to the student. Use view=student or view=parent to filter by receiver_type."""

    # Query Message model for messages targeted to this student
    from app.models.message import Message

    messages = db.query(Message).filter(
        Message.receiver_id == current_student.id,
        Message.receiver_type == view
    ).order_by(Message.created_at.desc()).all()

    result = []
    for msg in messages:
        result.append(StudentMessageItem(
            id=msg.id,
            subject=msg.subject,
            message=msg.message,
            from_educator=msg.sender.full_name if msg.sender else "",
            sent_at=convert_to_local_time(msg.created_at),
            is_read=msg.is_read,
            receiver_type=msg.receiver_type
        ))

    return result

@router.get("/scheduled-events", response_model=List[ScheduledEvent])
async def get_student_scheduled_events(
    current_student: Student = Depends(get_current_student), 
    db: Session = Depends(get_db)
):
    """Get scheduled events (both tasks and meetings) for the student"""
    import json
    
    # Get student's section and educator
    student_section = current_student.section
    if not student_section:
        return []  # If student has no section, they shouldn't see any events
        
    student_educator_id = student_section.educator_id
    scheduled_events = []
    
    print(f"🔍 Student {current_student.full_name} (ID: {current_student.id}) requesting scheduled events")
    print(f"📚 Student section: {student_section.name} (ID: {student_section.id})")
    print(f"👨‍🏫 Educator ID: {student_educator_id}")
    
    # 1. FETCH TASKS from Schedule table
    tasks = db.query(Schedule).filter(
        Schedule.start_datetime >= datetime.now(),
        Schedule.event_type == EventType.TASK,
        Schedule.educator_id == student_educator_id  # Only tasks from their educator
    ).order_by(Schedule.start_datetime).all()
    
    for task in tasks:
        # Parse participants JSON to check if this student should see this task
        should_include = True  # Default to include since we're only getting tasks from their educator
        
        if task.participants:
            try:
                participants_data = json.loads(task.participants)
                should_include = False  # Reset to false when participants are specified
                
                # Check if student is individually targeted
                if 'students' in participants_data:
                    student_emails = participants_data['students']
                    if current_student.email in student_emails:
                        should_include = True
                
                # Check if student's section is targeted
                if 'sections' in participants_data:
                    target_sections = participants_data['sections']
                    if current_student.section_id in target_sections:
                        should_include = True
                
                # Check if student's roll number is in targeted range
                if 'roll_range' in participants_data:
                    roll_range = participants_data['roll_range']
                    if 'start' in roll_range and 'end' in roll_range:
                        # Extract roll number from student email (e.g., S101@gmail.com -> 101)
                        student_roll = int(current_student.email.split('@')[0][1:])  # Remove 'S' prefix
                        if roll_range['start'] <= student_roll <= roll_range['end']:
                            should_include = True
                            
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # If participants parsing fails, include by default since it's from their educator
                should_include = True
        
        if should_include:
            scheduled_event = ScheduledEvent(
                id=task.id,
                title=task.title,
                description=task.description or "",
                event_type="task",
                start_datetime=task.start_datetime,
                end_datetime=task.end_datetime,
                location=task.location or "",
                educator_name=task.educator.full_name if task.educator else "System",
                status=task.status.value
            )
            scheduled_events.append(scheduled_event)
    
    # 2. FETCH MEETINGS from Meeting and MeetingRecipient tables
    try:
        print(f"🔍 Querying meetings for student {current_student.id} from educator {student_educator_id}")
        meetings = db.query(Meeting).join(MeetingRecipient).filter(
            Meeting.meeting_date >= datetime.now(),
            Meeting.is_active == True,
            Meeting.organizer_id == student_educator_id,  # Only meetings from their educator
            # Student is individually invited as a recipient
            MeetingRecipient.recipient_type == RecipientType.STUDENT,
            MeetingRecipient.recipient_id == current_student.id
        ).options(joinedload(Meeting.organizer)).order_by(Meeting.meeting_date).all()
        print(f"📅 Found {len(meetings)} meetings")
    except Exception as e:
        print(f"❌ Error querying meetings: {str(e)}")
        meetings = []
    
    for meeting in meetings:
        # Calculate end time
        end_time = meeting.meeting_date
        if meeting.duration_minutes:
            end_time = meeting.meeting_date + timedelta(minutes=meeting.duration_minutes)
        
        # Get RSVP status for this student
        rsvp_status = "pending"
        meeting_recipient = db.query(MeetingRecipient).filter(
            MeetingRecipient.meeting_id == meeting.id,
            MeetingRecipient.recipient_type == RecipientType.STUDENT,
            MeetingRecipient.recipient_id == current_student.id
        ).first()
        
        if meeting_recipient and meeting_recipient.rsvp_status:
            rsvp_status = meeting_recipient.rsvp_status.value
        
        scheduled_event = ScheduledEvent(
            id=meeting.id,
            title=meeting.title,
            description=meeting.description or "",
            event_type="meeting",
            start_datetime=meeting.meeting_date,
            end_datetime=end_time,
            location=meeting.location or "",
            educator_name=meeting.organizer.full_name if meeting.organizer else "System",
            status="scheduled",  # Meetings don't have status like tasks
            virtual_meeting_link=meeting.virtual_meeting_link,
            duration_minutes=meeting.duration_minutes,
            requires_rsvp=meeting.requires_rsvp,
            rsvp_status=rsvp_status
        )
        scheduled_events.append(scheduled_event)
    
    # Sort all events by start datetime
    scheduled_events.sort(key=lambda x: x.start_datetime)
    
    return scheduled_events

@router.post("/contact-teacher")
async def send_message_to_teacher(
    message_data: ContactTeacherMessage,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Send a message to a teacher"""
    
    # Create a new communication from student to educator
    communication = Communication(
        sender_id=None,  # Student doesn't have educator ID
        recipient_type="educator",
        recipient_id=message_data.recipient_educator_id,
        subject=message_data.subject,
        message=f"From Student: {current_student.full_name} ({current_student.email})\n\n{message_data.message}",
        message_type="student_query",
        sent_at=datetime.now()
    )
    
    db.add(communication)
    db.commit()
    
    return {"message": "Message sent successfully to teacher"}

@router.get("/profile")
async def get_detailed_student_profile(current_student: Student = Depends(get_current_student)):
    """Get detailed student profile information"""
    
    return {
        "id": current_student.id,
        "student_id": current_student.student_id,
        "name": current_student.full_name,
        "first_name": current_student.first_name,
        "last_name": current_student.last_name,
        "email": current_student.email,
        "roll_number": current_student.roll_number,
        "section": {
            "id": current_student.section.id if current_student.section else None,
            "name": current_student.section.name if current_student.section else "No Section",
            "academic_year": current_student.section.academic_year if current_student.section else None,
            "semester": current_student.section.semester if current_student.section else None
        },
        "contact": {
            "phone": current_student.phone or "",
            "guardian_email": current_student.guardian_email or ""
        },
        "status": "Active" if current_student.is_active else "Inactive",
        "created_at": current_student.created_at
    }

# ==================== REPORT FUNCTIONALITY ====================

@router.get("/reports", response_model=List[ReceivedReport])
async def get_student_reports(
    current_student: Student = Depends(get_current_student), 
    db: Session = Depends(get_db)
):
    """Get all reports sent to the student"""
    
    reports = db.query(SentReport).filter(
        SentReport.student_id == current_student.id,
        or_(
            SentReport.recipient_type == ReportRecipientType.STUDENT,
            SentReport.recipient_type == ReportRecipientType.BOTH
        )
    ).order_by(SentReport.sent_at.desc()).all()
    
    result = []
    for report in reports:
        result.append(ReceivedReport(
            id=report.id,
            report_type=report.report_type.value,
            title=report.title,
            description=report.description or "",
            from_educator=f"{report.educator.first_name} {report.educator.last_name}",
            sent_at=report.sent_at,
            is_viewed_by_student=report.is_viewed_by_student,
            is_viewed_by_parent=report.is_viewed_by_parent,
            recipient_type=report.recipient_type.value,
            report_format=report.report_format,
            comments=report.comments,
            academic_year=report.academic_year
            ,
            download_url=f"/api/v1/student-dashboard/reports/{report.id}/download"
        ))
    
    return result

@router.get("/parent-reports", response_model=List[ParentModeReport])
async def get_parent_reports(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get reports for parent view (when student is in parent mode)"""
    
    reports = db.query(SentReport).filter(
        SentReport.student_id == current_student.id,
        or_(
            SentReport.recipient_type == ReportRecipientType.PARENT,
            SentReport.recipient_type == ReportRecipientType.BOTH
        )
    ).order_by(SentReport.sent_at.desc()).all()
    
    result = []
    for report in reports:
        result.append(ParentModeReport(
            id=report.id,
            report_type=report.report_type.value,
            title=report.title,
            description=report.description or "",
            from_educator=f"{report.educator.first_name} {report.educator.last_name}",
            sent_at=report.sent_at,
            is_viewed_by_parent=report.is_viewed_by_parent,
            recipient_type=report.recipient_type.value,
            report_format=report.report_format,
            comments=report.comments,
            academic_year=report.academic_year,
            student_name=current_student.full_name
            ,
            download_url=f"/api/v1/student-dashboard/reports/{report.id}/download"
        ))
    
    return result

@router.post("/reports/{report_id}/mark-viewed")
async def mark_report_as_viewed(
    report_id: int,
    viewer_type: Literal["student", "parent"] = "student",
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Mark a report as viewed by student or parent"""
    
    report = db.query(SentReport).filter(
        SentReport.id == report_id,
        SentReport.student_id == current_student.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Update viewed status
    if viewer_type == "student":
        report.is_viewed_by_student = True
        report.student_viewed_at = datetime.now()
    elif viewer_type == "parent":
        report.is_viewed_by_parent = True
        report.parent_viewed_at = datetime.now()
    
    # Update overall status
    if report.recipient_type.value == "both":
        if report.is_viewed_by_student and report.is_viewed_by_parent:
            report.status = ReportStatus.VIEWED
            report.viewed_at = datetime.now()
    else:
        report.status = ReportStatus.VIEWED
        report.viewed_at = datetime.now()
    
    db.commit()
    
    return {"message": f"Report marked as viewed by {viewer_type}"}

@router.get("/reports/{report_id}/download")
async def download_student_report(
    report_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Download a specific report file"""
    
    report = db.query(SentReport).filter(
        SentReport.id == report_id,
        SentReport.student_id == current_student.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.report_file_path or not os.path.exists(report.report_file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Determine media type based on format
    media_type = "application/pdf" if report.report_format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return FileResponse(
        path=report.report_file_path,
        filename=f"{report.title}_{report.sent_at.strftime('%Y%m%d')}.{report.report_format}",
        media_type=media_type
    )