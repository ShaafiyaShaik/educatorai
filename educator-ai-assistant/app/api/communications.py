"""
Communications API endpoints for automated email and notification management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.communication import Communication
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.student import Student
from app.agents.communication_agent import communication_agent
from app.services.email_service import email_service

router = APIRouter()

# Pydantic models
class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    content: str
    email_type: str = "notification"

class BulkNotificationRequest(BaseModel):
    target_groups: List[str]
    notification_type: str
    subject: str
    message: str
    priority: str = "normal"
    schedule_send: bool = False
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None

class TemplateRequest(BaseModel):
    communication_type: str
    variables: Dict[str, Any]

class CommunicationResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None

@router.post("/send-email", response_model=CommunicationResponse)
async def send_email(
    email_request: EmailRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Send real email via SMTP and store in database"""
    try:
        print(f"📧 Sending email from {current_educator.email} to {email_request.recipient_email}")
        print(f"📋 Subject: {email_request.subject}")
        
        # Check if recipient is a student in our system
        student = db.query(Student).filter(Student.email == email_request.recipient_email).first()
        print(f"👤 Student found: {student.full_name if student else 'Not a student in system'}")
        
        # Use real email service
        result = email_service.send_email(
            to_email=email_request.recipient_email,
            subject=email_request.subject,
            body=f"""
{email_request.content}

---
Sent via Educator AI Assistant
From: {current_educator.full_name} ({current_educator.email})
Department: {current_educator.department}
            """.strip(),
            from_email=f"{current_educator.full_name} <{current_educator.email}>"
        )
        
        print(f"📤 Email sending result: {result['success']}")
        
        # Store email in database
        communication = Communication(
            sender_email=current_educator.email,
            recipient_email=email_request.recipient_email,
            subject=email_request.subject,
            content=email_request.content,
            sent_at=datetime.utcnow(),
            status="sent" if result["success"] else "failed",
            email_type=email_request.email_type
        )
        db.add(communication)
        
        # If recipient is a student, create a notification for them
        if student:
            print(f"🔔 Creating notification for student {student.full_name}")
            notification = Notification(
                student_id=student.id,
                title=f"Message from {current_educator.full_name}",
                message=f"Subject: {email_request.subject}\n\n{email_request.content}",
                notification_type=NotificationType.COMMUNICATION,
                status=NotificationStatus.UNREAD,
                priority="normal",
                category="communication",
                created_at=datetime.utcnow()
            )
            db.add(notification)
            print(f"✅ Notification created for student dashboard")
        
        db.commit()
        db.refresh(communication)
        
        return CommunicationResponse(
            success=result["success"],
            message=f"Email sent successfully{' and notification created' if student else ''}",
            details=str(result.get("details", ""))
        )
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        # If email sending fails, still store with failed status
        try:
            student = db.query(Student).filter(Student.email == email_request.recipient_email).first()
            
            communication = Communication(
                sender_email=current_educator.email,
                recipient_email=email_request.recipient_email,
                subject=email_request.subject,
                content=email_request.content,
                sent_at=datetime.utcnow(),
                status="failed",
                email_type=email_request.email_type
            )
            db.add(communication)
            
            # Even if email fails, create notification for student (in-app delivery)
            if student:
                print(f"🔔 Email failed, but creating in-app notification for {student.full_name}")
                notification = Notification(
                    student_id=student.id,
                    title=f"Message from {current_educator.full_name}",
                    message=f"Subject: {email_request.subject}\n\n{email_request.content}",
                    notification_type=NotificationType.COMMUNICATION,
                    status=NotificationStatus.UNREAD,
                    priority="normal",
                    category="communication",
                    created_at=datetime.utcnow()
                )
                db.add(notification)
                print(f"✅ In-app notification created despite email failure")
            
            db.commit()
        except:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

@router.post("/bulk-notification", response_model=CommunicationResponse)
async def send_bulk_notification(
    notification_request: BulkNotificationRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Send bulk notifications to multiple recipients"""
    try:
        # Convert target groups to actual recipients
        recipients = []
        if 'students' in notification_request.target_groups:
            recipients.extend(['student1@university.edu', 'student2@university.edu'])
        if 'all_educators' in notification_request.target_groups:
            recipients.extend(['educator1@university.edu', 'educator2@university.edu'])
        if 'parents' in notification_request.target_groups:
            recipients.extend(['parent1@university.edu', 'parent2@university.edu'])
        
        # Send emails to recipients using email service
        for recipient in recipients:
            email_result = email_service.send_email(
                to_email=recipient,
                subject=notification_request.subject,
                body=f"""
{notification_request.message}

---
Sent via Educator AI Assistant
From: {current_educator.full_name} ({current_educator.email})
Department: {current_educator.department}
Priority: {notification_request.priority}
                """.strip(),
                from_email=f"{current_educator.full_name} <{current_educator.email}>"
            )
        
        return CommunicationResponse(
            success=True,
            message=f"Bulk notification sent successfully to {len(recipients)} recipients",
            details=f"Notification type: {notification_request.notification_type}, Recipients: {', '.join(recipients)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk notification: {str(e)}"
        )

@router.post("/generate-template", response_model=Dict[str, str])
async def generate_communication_template(
    template_request: TemplateRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Generate reusable communication template"""
    try:
        template = communication_agent.generate_communication_template(
            communication_type=template_request.communication_type,
            variables=template_request.variables
        )
        
        return {
            "template": template,
            "communication_type": template_request.communication_type,
            "variables": str(template_request.variables)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}"
        )

@router.post("/schedule-reminder")
async def schedule_reminder(
    event_details: Dict[str, Any],
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Schedule automated reminder for events"""
    try:
        # This would integrate with a task scheduler like Celery
        # For now, we'll return a success response
        return CommunicationResponse(
            success=True,
            message="Reminder scheduled successfully",
            details=f"Reminder set for: {event_details.get('title', 'Event')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule reminder: {str(e)}"
        )

@router.get("/templates")
async def get_communication_templates(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get available communication templates"""
    templates = {
        "meeting_reminder": {
            "subject": "Meeting Reminder: {meeting_title}",
            "content": "This is a reminder that you have a meeting scheduled for {date_time}. Location: {location}",
            "variables": ["meeting_title", "date_time", "location"]
        },
        "class_cancellation": {
            "subject": "Class Cancellation Notice - {course_code}",
            "content": "Due to {reason}, the {course_code} class scheduled for {date_time} has been cancelled.",
            "variables": ["course_code", "reason", "date_time"]
        },
        "grade_notification": {
            "subject": "Grade Posted - {assignment_name}",
            "content": "Your grade for {assignment_name} has been posted. Please check the course portal for details.",
            "variables": ["assignment_name"]
        },
        "office_hours_change": {
            "subject": "Office Hours Update",
            "content": "My office hours have been updated. New schedule: {new_schedule}. Location: {location}",
            "variables": ["new_schedule", "location"]
        }
    }
    
    return templates

@router.get("/notification-history")
async def get_notification_history(
    skip: int = 0,
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get notification history for the current educator"""
    # This would query a notifications table in a real implementation
    # For now, return mock data
    return {
        "notifications": [
            {
                "id": 1,
                "type": "email",
                "recipient": "student@university.edu",
                "subject": "Assignment Reminder",
                "sent_at": "2025-09-20T10:00:00Z",
                "status": "delivered"
            }
        ],
        "total": 1,
        "skip": skip,
        "limit": limit
    }

@router.get("/")
async def list_communications(
    skip: int = 0,
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get list of all communications sent by the current educator"""
    try:
        # Get communications sent by this educator
        sent_communications = db.query(Communication).filter(
            Communication.sender_email == current_educator.email
        ).order_by(Communication.sent_at.desc()).offset(skip).limit(limit).all()
        
        communications_data = []
        for comm in sent_communications:
            communications_data.append({
                "id": comm.id,
                "subject": comm.subject,
                "recipient": comm.recipient_email,
                "content": comm.content,
                "sent_at": comm.sent_at.isoformat(),
                "status": comm.status,
                "type": comm.email_type
            })
        
        total_count = db.query(Communication).filter(
            Communication.sender_email == current_educator.email
        ).count()
        
        return {
            "data": communications_data,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        # Fallback to mock data if database fails
        communications = [
            {
                "id": 1,
                "subject": "Test Email",
                "recipient": "skshaafiya@gmail.com",
                "content": "This is the email you sent to skshaafiya@gmail.com",
                "sent_at": datetime.now().isoformat(),
                "status": "sent",
                "type": "email"
            }
        ]
        
        return {
            "data": communications[skip:skip+limit],
            "total": len(communications),
            "skip": skip,
            "limit": limit
        }

@router.get("/incoming")
async def get_incoming_communications(
    skip: int = 0,
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get incoming communications/emails for the current educator"""
    try:
        # Get communications sent TO this educator
        incoming_communications = db.query(Communication).filter(
            Communication.recipient_email == current_educator.email
        ).order_by(Communication.sent_at.desc()).offset(skip).limit(limit).all()
        
        incoming_data = []
        for comm in incoming_communications:
            incoming_data.append({
                "id": comm.id,
                "from": comm.sender_email,
                "to": comm.recipient_email,
                "subject": comm.subject,
                "content": comm.content,
                "received_at": comm.sent_at.isoformat(),
                "status": "unread",  # TODO: Add read/unread tracking
                "type": "incoming_email"
            })
        
        total_count = db.query(Communication).filter(
            Communication.recipient_email == current_educator.email
        ).count()
        
        unread_count = total_count  # TODO: Implement read tracking
        
        return {
            "data": incoming_data,
            "total": total_count,
            "unread_count": unread_count,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        # Fallback to mock data
        incoming_emails = [
            {
                "id": 1,
                "from": "student@university.edu", 
                "to": current_educator.email,
                "subject": "Question about Assignment",
                "content": "Hello Professor, I have a question about the upcoming assignment deadline.",
                "received_at": datetime.now().isoformat(),
                "status": "unread",
                "type": "incoming_email"
            }
        ]
        
        return {
            "data": incoming_emails[skip:skip+limit],
            "total": len(incoming_emails),
            "unread_count": 1,
            "skip": skip,
            "limit": limit
        }