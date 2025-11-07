"""
Student Messaging API
Handles messages between educators and students
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.student import Student
from app.models.message import Message, MessageTemplate
from app.models.notification import Notification, NotificationType
from app.models.report import SentReport, RecipientType, ReportType

router = APIRouter()

# Pydantic models
class MessageCreate(BaseModel):
    receiver_id: int
    receiver_type: str = "student"  # student, parent, both
    subject: str
    message: str
    message_type: str = "general"  # general, academic, behavioral, attendance
    priority: str = "normal"  # low, normal, high, urgent
    is_report: bool = False

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    receiver_id: int
    receiver_name: str
    receiver_type: str
    subject: str
    message: str
    message_type: str
    priority: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageTemplateCreate(BaseModel):
    template_name: str
    subject_template: str
    message_template: str
    message_type: str = "general"

class MessageTemplateResponse(BaseModel):
    id: int
    template_name: str
    subject_template: str
    message_template: str
    message_type: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentMessageSummary(BaseModel):
    student_id: int
    student_name: str
    unread_count: int
    last_message_date: Optional[datetime]
    last_message_preview: str

@router.post("/send", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Send a message to a student"""
    
    # Verify the student exists and is in educator's sections
    student = db.query(Student).filter(Student.id == message_data.receiver_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if educator has access to this student
    educator_sections = db.query(Student.section_id).filter(
        Student.section_id.in_(
            db.query(Student.section_id).filter(Student.id == student.id)
        )
    ).first()
    
    # If this is a report, create a SentReport and a notification for the student
    if getattr(message_data, 'is_report', False):
        # Map receiver_type to RecipientType enum
        rec_type = message_data.receiver_type
        if rec_type == 'student':
            recipient_enum = RecipientType.STUDENT
        elif rec_type == 'parent':
            recipient_enum = RecipientType.PARENT
        else:
            recipient_enum = RecipientType.BOTH

        sent_report = SentReport(
            report_type=ReportType.INDIVIDUAL_STUDENT,
            title=message_data.subject,
            description=message_data.message,
            educator_id=current_educator.id,
            student_id=message_data.receiver_id,
            recipient_type=recipient_enum,
            report_data={"message": message_data.message}
        )

        db.add(sent_report)
        db.commit()
        db.refresh(sent_report)

        # Create a Notification so the student sees it in notifications
        try:
            notification = Notification(
                educator_id=current_educator.id,
                student_id=message_data.receiver_id,
                title=f"Report: {message_data.subject}",
                message=message_data.message,
                notification_type=NotificationType.GRADE_REPORT,
                status=None,
                additional_data=None
            )
            db.add(notification)
            db.commit()
        except Exception:
            db.rollback()

        # Return a simpler response object for reports
        return {
            "id": sent_report.id,
            "sender_id": current_educator.id,
            "sender_name": f"{current_educator.first_name} {current_educator.last_name}",
            "receiver_id": sent_report.student_id,
            "receiver_name": f"{student.first_name} {student.last_name}",
            "receiver_type": message_data.receiver_type,
            "subject": sent_report.title,
            "message": sent_report.description,
            "message_type": message_data.message_type,
            "priority": message_data.priority,
            "is_report": True,
            "created_at": sent_report.sent_at
        }

    # Otherwise create a standard Message and optionally create a Notification for parent-targeted messages
    message = Message(
        sender_id=current_educator.id,
        receiver_id=message_data.receiver_id,
        receiver_type=message_data.receiver_type,
        subject=message_data.subject,
        message=message_data.message,
        message_type=message_data.message_type,
        priority=message_data.priority
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    # If message is targeted to parent (or both), create a Notification record tied to the student
    try:
        if message.receiver_type in ('parent', 'both'):
            notification = Notification(
                educator_id=current_educator.id,
                student_id=message.receiver_id,
                title=message.subject,
                message=message.message,
                notification_type=NotificationType.COMMUNICATION,
                status=None,
                additional_data=None
            )
            db.add(notification)
            db.commit()
    except Exception:
        db.rollback()

    # Format response
    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=f"{current_educator.first_name} {current_educator.last_name}",
        receiver_id=message.receiver_id,
        receiver_name=f"{student.first_name} {student.last_name}",
        receiver_type=message.receiver_type,
        subject=message.subject,
        message=message.message,
        message_type=message.message_type,
        priority=message.priority,
        is_read=message.is_read,
        read_at=message.read_at,
        created_at=message.created_at
    )

@router.get("/sent", response_model=List[MessageResponse])
async def get_sent_messages(
    student_id: Optional[int] = None,
    message_type: Optional[str] = None,
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get messages sent by the educator"""
    
    query = db.query(Message).filter(Message.sender_id == current_educator.id)
    
    if student_id:
        query = query.filter(Message.receiver_id == student_id)
    
    if message_type:
        query = query.filter(Message.message_type == message_type)
    
    messages = query.options(
        joinedload(Message.receiver)
    ).order_by(desc(Message.created_at)).limit(limit).all()
    
    return [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=f"{current_educator.first_name} {current_educator.last_name}",
            receiver_id=msg.receiver_id,
            receiver_name=f"{msg.receiver.first_name} {msg.receiver.last_name}",
            receiver_type=msg.receiver_type,
            subject=msg.subject,
            message=msg.message,
            message_type=msg.message_type,
            priority=msg.priority,
            is_read=msg.is_read,
            read_at=msg.read_at,
            created_at=msg.created_at
        )
        for msg in messages
    ]

@router.get("/student/{student_id}/conversation", response_model=List[MessageResponse])
async def get_student_conversation(
    student_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get conversation history with a specific student"""
    
    # Verify student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    messages = db.query(Message).filter(
        and_(
            Message.sender_id == current_educator.id,
            Message.receiver_id == student_id
        )
    ).options(
        joinedload(Message.receiver)
    ).order_by(desc(Message.created_at)).all()
    
    return [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=f"{current_educator.first_name} {current_educator.last_name}",
            receiver_id=msg.receiver_id,
            receiver_name=f"{msg.receiver.first_name} {msg.receiver.last_name}",
            receiver_type=msg.receiver_type,
            subject=msg.subject,
            message=msg.message,
            message_type=msg.message_type,
            priority=msg.priority,
            is_read=msg.is_read,
            read_at=msg.read_at,
            created_at=msg.created_at
        )
        for msg in messages
    ]

@router.get("/students/summary", response_model=List[StudentMessageSummary])
async def get_students_message_summary(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get message summary for all students in educator's sections"""
    
    # Get all students in educator's sections
    students = db.query(Student).filter(
        Student.section_id.in_(
            db.query(Student.section_id).distinct()
        )
    ).all()
    
    summaries = []
    for student in students:
        # Get unread message count
        unread_count = db.query(Message).filter(
            and_(
                Message.sender_id == current_educator.id,
                Message.receiver_id == student.id,
                Message.is_read == False
            )
        ).count()
        
        # Get last message
        last_message = db.query(Message).filter(
            and_(
                Message.sender_id == current_educator.id,
                Message.receiver_id == student.id
            )
        ).order_by(desc(Message.created_at)).first()
        
        preview = ""
        last_date = None
        if last_message:
            preview = last_message.message[:50] + "..." if len(last_message.message) > 50 else last_message.message
            last_date = last_message.created_at
        
        summaries.append(StudentMessageSummary(
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            unread_count=unread_count,
            last_message_date=last_date,
            last_message_preview=preview
        ))
    
    return summaries

# Message Templates
@router.post("/templates", response_model=MessageTemplateResponse)
async def create_message_template(
    template_data: MessageTemplateCreate,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create a message template"""
    
    template = MessageTemplate(
        educator_id=current_educator.id,
        template_name=template_data.template_name,
        subject_template=template_data.subject_template,
        message_template=template_data.message_template,
        message_type=template_data.message_type
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return MessageTemplateResponse(
        id=template.id,
        template_name=template.template_name,
        subject_template=template.subject_template,
        message_template=template.message_template,
        message_type=template.message_type,
        is_active=template.is_active,
        created_at=template.created_at
    )

@router.get("/templates", response_model=List[MessageTemplateResponse])
async def get_message_templates(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get educator's message templates"""
    
    templates = db.query(MessageTemplate).filter(
        and_(
            MessageTemplate.educator_id == current_educator.id,
            MessageTemplate.is_active == True
        )
    ).order_by(MessageTemplate.template_name).all()
    
    return [
        MessageTemplateResponse(
            id=template.id,
            template_name=template.template_name,
            subject_template=template.subject_template,
            message_template=template.message_template,
            message_type=template.message_type,
            is_active=template.is_active,
            created_at=template.created_at
        )
        for template in templates
    ]

@router.put("/mark-read/{message_id}")
async def mark_message_read(
    message_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Mark a message as read (for student replies)"""
    
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.is_read = True
    message.read_at = datetime.now()
    db.commit()
    
    return {"message": "Message marked as read"}

@router.get("/quick-messages")
async def get_quick_message_options():
    """Get predefined quick message options"""
    
    return {
        "academic": [
            "Great improvement in recent assignments!",
            "Please see me after class to discuss your progress.",
            "Assignment due date reminder",
            "Excellent work on the recent project!"
        ],
        "behavioral": [
            "Thank you for your positive attitude in class.",
            "Please remember to follow classroom guidelines.",
            "Your participation has been outstanding!",
            "Let's work together to improve classroom behavior."
        ],
        "attendance": [
            "Please ensure regular attendance for better learning.",
            "Missed assignments due to absence - please catch up.",
            "Your attendance has been excellent this month!",
            "Please contact me regarding recent absences."
        ],
        "general": [
            "Keep up the good work!",
            "Please remember to bring your materials to class.",
            "Great to see your enthusiasm for learning!",
            "Please see me during office hours."
        ]
    }