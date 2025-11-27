"""Action Engine API

Exposes internal, authenticated endpoints that perform concrete actions inside
the system. These endpoints are the only routes Gemini should ever call via
your internal intent router / executor. Gemini itself never performs these
actions directly.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.message import Message
from app.models.notification import Notification, NotificationType
from app.models.meeting_schedule import Meeting, MeetingRecipient, RecipientType
from app.models.performance import Attendance, Exam
from app.models.report import SentReport, ReportType, RecipientType as ReportRecipientType
from app.services.email_service import email_service
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    receiver_id: int
    receiver_type: str = "student"
    subject: Optional[str] = "Message from educator"
    message: str
    message_type: Optional[str] = "general"


@router.post("/send_message")
def send_message(payload: SendMessageRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    """Create an in-app message and notification for a student/parent."""
    msg = Message(
        sender_id=current_educator.id,
        receiver_id=payload.receiver_id,
        receiver_type=payload.receiver_type,
        subject=payload.subject,
        message=payload.message,
        message_type=payload.message_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Create a notification for the student to surface in their dashboard
    try:
        note = Notification(
            student_id=payload.receiver_id if payload.receiver_type == "student" else None,
            educator_id=current_educator.id if payload.receiver_type != "student" else None,
            title=payload.subject,
            message=payload.message,
            notification_type=NotificationType.COMMUNICATION,
        )
        db.add(note)
        db.commit()
        db.refresh(note)
    except Exception:
        logger.exception("Failed to create notification for message")

    return {"status": "ok", "message_id": msg.id, "detail": "Message created"}


class ScheduleMeetingRequest(BaseModel):
    title: str
    meeting_date: Optional[str]
    duration_minutes: Optional[int] = 60
    student_ids: List[int]
    notify_parents: Optional[bool] = False


@router.post("/schedule_meeting")
def schedule_meeting(payload: ScheduleMeetingRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    meeting = Meeting(
        organizer_id=current_educator.id,
        title=payload.title,
        description="Scheduled via chatbot",
        meeting_date=payload.meeting_date,
        duration_minutes=payload.duration_minutes,
        meeting_type="INDIVIDUAL" if len(payload.student_ids) == 1 else "SECTION",
        notify_parents=payload.notify_parents,
        send_immediately=True,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # Create recipients
    for sid in payload.student_ids:
        rec = MeetingRecipient(
            meeting_id=meeting.id,
            recipient_id=sid,
            recipient_type=RecipientType.STUDENT,
        )
        db.add(rec)
    db.commit()

    return {"status": "ok", "meeting_id": meeting.id, "detail": "Meeting scheduled"}


class NotifyStudentRequest(BaseModel):
    student_id: int
    title: str
    message: str
    category: Optional[str] = "announcement"


@router.post("/notify_student")
def notify_student(payload: NotifyStudentRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    note = Notification(
        student_id=payload.student_id,
        educator_id=current_educator.id,
        title=payload.title,
        message=payload.message,
        notification_type=NotificationType.ANNOUNCEMENT,
        category=payload.category,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"status": "ok", "notification_id": note.id}


class DashboardAlertRequest(BaseModel):
    title: str
    message: str
    section_id: Optional[int]


@router.post("/post_dashboard_alert")
def post_dashboard_alert(payload: DashboardAlertRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    # For Phase 2 we create a Notification categorized as a dashboard alert.
    note = Notification(
        educator_id=current_educator.id,
        title=payload.title,
        message=payload.message,
        notification_type=NotificationType.ANNOUNCEMENT,
        category="dashboard_alert",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"status": "ok", "notification_id": note.id}


class UpdateAttendanceRequest(BaseModel):
    student_id: int
    date: str
    present: bool
    reason: Optional[str]


@router.post("/update_attendance")
def update_attendance(payload: UpdateAttendanceRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    att = Attendance(
        student_id=payload.student_id,
        date=payload.date,
        status="present" if payload.present else "absent",
        remarks=payload.reason or None,
        educator_id=current_educator.id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return {"status": "ok", "attendance_id": att.id}


class EmailParentRequest(BaseModel):
    parent_email: str
    subject: str
    body: str
    student_id: Optional[int]


@router.post("/email_parent")
def email_parent(payload: EmailParentRequest, current_educator=Depends(get_current_educator)):
    res = email_service.send_email(payload.parent_email, payload.subject, payload.body)
    return {"status": "ok" if res.get("success") else "error", "detail": res}


class EvaluateExamRequest(BaseModel):
    exam_id: int
    student_ids: List[int]


@router.post("/evaluate_exam")
def evaluate_exam(payload: EvaluateExamRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    # Simplified evaluation: in a real system this would compute grades, update records,
    # and maybe send notifications. For Phase 2 we simulate and create a SentReport.
    report = SentReport(
        report_type=ReportType.INDIVIDUAL_STUDENT,
        title=f"Exam {payload.exam_id} evaluation",
        description="Automated exam evaluation",
        educator_id=current_educator.id,
        report_data={"exam_id": payload.exam_id, "students": payload.student_ids},
        recipient_type=ReportRecipientType.STUDENT,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"status": "ok", "report_id": report.id}


class BulkSendSectionReportsRequest(BaseModel):
    section_id: int
    title: str
    body: str


@router.post("/bulk_send_section_reports")
def bulk_send_section_reports(payload: BulkSendSectionReportsRequest, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    # Query students in section
    students = db.execute("SELECT id, email FROM students WHERE section_id = :sid", {"sid": payload.section_id}).fetchall()
    emails = [s.email for s in students if getattr(s, 'email', None)]
    res = email_service.send_bulk_email(emails, payload.title, payload.body)

    # store a SentReport for traceability
    report = SentReport(
        report_type=ReportType.SECTION_SUMMARY,
        title=payload.title,
        description=payload.body,
        educator_id=current_educator.id,
        section_id=payload.section_id,
        recipient_type=ReportRecipientType.PARENT,
        report_data={"result": res},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"status": "ok", "detail": res, "report_id": report.id}
