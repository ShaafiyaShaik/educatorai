"""
Meeting scheduling API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models import Meeting, MeetingRecipient, Student, Section, Educator
from app.models.meeting_schedule import MeetingType, RecipientType, DeliveryStatus, RSVPStatus
from app.api.educators import get_current_educator

router = APIRouter()

# Pydantic Models
class MeetingCreate(BaseModel):
    title: str = Field(..., max_length=200, description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    meeting_date: Optional[datetime] = Field(None, description="Meeting date and time")
    duration_minutes: int = Field(60, ge=15, le=480, description="Duration in minutes")
    location: Optional[str] = Field(None, max_length=200, description="Meeting location")
    virtual_meeting_link: Optional[str] = Field(None, max_length=500, description="Virtual meeting link")
    
    # Meeting configuration
    meeting_type: MeetingType = Field(..., description="Type of meeting")
    section_id: Optional[int] = Field(None, description="Section ID if section meeting")
    student_ids: Optional[List[int]] = Field(default=[], description="Individual student IDs")
    notify_parents: bool = Field(True, description="Whether to notify parents")
    requires_rsvp: bool = Field(False, description="Whether RSVP is required")
    send_reminders: bool = Field(True, description="Whether to send reminders")
    reminder_minutes_before: int = Field(60, ge=5, le=1440, description="Reminder time in minutes")
    
    # Scheduling
    send_immediately: bool = Field(True, description="Send immediately or schedule")
    scheduled_send_at: Optional[datetime] = Field(None, description="When to send if scheduled")
    
    # Attachments
    attachments: Optional[List[str]] = Field(default=[], description="Attachment URLs")

class MeetingResponse(BaseModel):
    id: int
    organizer_id: int
    title: str
    description: Optional[str]
    meeting_date: Optional[datetime]
    duration_minutes: int
    location: Optional[str]
    virtual_meeting_link: Optional[str]
    meeting_type: MeetingType
    section_id: Optional[int]
    notify_parents: bool
    requires_rsvp: bool
    send_reminders: bool
    reminder_minutes_before: int
    send_immediately: bool
    scheduled_send_at: Optional[datetime]
    attachments: List[str]
    is_active: bool
    created_at: datetime
    sent_at: Optional[datetime]
    recipient_count: int

class RecipientResponse(BaseModel):
    id: int
    recipient_id: int
    recipient_type: RecipientType
    recipient_name: str
    recipient_email: str
    delivery_status: DeliveryStatus
    rsvp_status: RSVPStatus
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    rsvp_at: Optional[datetime]
    rsvp_message: Optional[str]

@router.post("/", response_model=MeetingResponse)
async def create_meeting(
    meeting_data: MeetingCreate,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create a new meeting and schedule it for delivery"""
    
    # Validation
    if meeting_data.meeting_type == MeetingType.SECTION and not meeting_data.section_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section ID required for section meetings"
        )
    
    if meeting_data.meeting_type == MeetingType.INDIVIDUAL and not meeting_data.student_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student IDs required for individual meetings"
        )
    
    # Verify section belongs to educator
    if meeting_data.section_id:
        section = db.query(Section).filter(
            Section.id == meeting_data.section_id,
            Section.educator_id == current_educator.id
        ).first()
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
    
    # Create meeting
    meeting = Meeting(
        organizer_id=current_educator.id,
        title=meeting_data.title,
        description=meeting_data.description,
        meeting_date=meeting_data.meeting_date,
        duration_minutes=meeting_data.duration_minutes,
        location=meeting_data.location,
        virtual_meeting_link=meeting_data.virtual_meeting_link,
        meeting_type=meeting_data.meeting_type,
        section_id=meeting_data.section_id,
        notify_parents=meeting_data.notify_parents,
        requires_rsvp=meeting_data.requires_rsvp,
        send_reminders=meeting_data.send_reminders,
        reminder_minutes_before=meeting_data.reminder_minutes_before,
        send_immediately=meeting_data.send_immediately,
        scheduled_send_at=meeting_data.scheduled_send_at,
        attachments=meeting_data.attachments or []
    )
    
    db.add(meeting)
    db.flush()  # Get the ID
    
    # Resolve recipients
    recipients = []
    
    if meeting_data.meeting_type == MeetingType.SECTION:
        # Get all students in the section
        students = db.query(Student).filter(Student.section_id == meeting_data.section_id).all()
    elif meeting_data.meeting_type == MeetingType.INDIVIDUAL:
        # Get specific students
        students = db.query(Student).filter(Student.id.in_(meeting_data.student_ids)).all()
        
        # Verify students belong to educator's sections
        valid_section_ids = [s.id for s in current_educator.sections]
        invalid_students = [s for s in students if s.section_id not in valid_section_ids]
        
        if invalid_students:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to students: {[s.student_id for s in invalid_students]}"
            )
    else:
        students = []
    
    # Add student recipients
    for student in students:
        recipient = MeetingRecipient(
            meeting_id=meeting.id,
            recipient_id=student.id,
            recipient_type=RecipientType.STUDENT
        )
        recipients.append(recipient)
        
        # Add parent recipients if enabled
        if meeting_data.notify_parents:
            # Get parents for this student (assuming parent relationship exists)
            # For now, we'll create placeholder parent recipients
            # You'd need to implement parent-student relationships
            pass
    
    # Add all recipients to database
    db.add_all(recipients)
    
    # Mark as sent if sending immediately
    if meeting_data.send_immediately:
        meeting.sent_at = datetime.utcnow()
        for recipient in recipients:
            recipient.delivery_status = DeliveryStatus.SENT
            recipient.sent_at = meeting.sent_at
    
    db.commit()
    db.refresh(meeting)
    
    # Return response
    response_data = meeting.to_dict()
    response_data["recipient_count"] = len(recipients)
    
    return MeetingResponse(**response_data)

@router.get("/", response_model=List[MeetingResponse])
async def get_my_meetings(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all meetings created by the current educator"""
    
    meetings = db.query(Meeting).filter(
        Meeting.organizer_id == current_educator.id,
        Meeting.is_active == True
    ).order_by(Meeting.created_at.desc()).all()
    
    result = []
    for meeting in meetings:
        data = meeting.to_dict()
        data["recipient_count"] = len(meeting.recipients)
        result.append(MeetingResponse(**data))
    
    return result

@router.get("/{meeting_id}/recipients", response_model=List[RecipientResponse])
async def get_meeting_recipients(
    meeting_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get recipients and their status for a specific meeting"""
    
    # Verify meeting belongs to educator
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.organizer_id == current_educator.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get recipients with student/parent info
    recipients = db.query(MeetingRecipient).filter(
        MeetingRecipient.meeting_id == meeting_id
    ).all()
    
    result = []
    for recipient in recipients:
        if recipient.recipient_type == RecipientType.STUDENT:
            student = db.query(Student).get(recipient.recipient_id)
            if student:
                result.append(RecipientResponse(
                    id=recipient.id,
                    recipient_id=recipient.recipient_id,
                    recipient_type=recipient.recipient_type,
                    recipient_name=f"{student.first_name} {student.last_name}",
                    recipient_email=student.email,
                    delivery_status=recipient.delivery_status,
                    rsvp_status=recipient.rsvp_status,
                    sent_at=recipient.sent_at,
                    read_at=recipient.read_at,
                    rsvp_at=recipient.rsvp_at,
                    rsvp_message=recipient.rsvp_message
                ))
        # TODO: Add parent handling when parent model is available
    
    return result

@router.delete("/{meeting_id}")
async def cancel_meeting(
    meeting_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Cancel a meeting (soft delete)"""
    
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.organizer_id == current_educator.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    meeting.is_active = False
    db.commit()
    
    return {"message": "Meeting cancelled successfully"}

@router.get("/my-sections", response_model=List[dict])
async def get_my_sections_for_meetings(
    include_students: bool = True,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get educator's sections for meeting creation"""
    
    print(f"🔍 API my-sections called for educator {current_educator.id}, include_students={include_students}")
    
    sections = db.query(Section).filter(Section.educator_id == current_educator.id).all()
    print(f"📚 Found {len(sections)} sections for educator")
    
    result = []
    for section in sections:
        students_query = db.query(Student).filter(Student.section_id == section.id)
        student_count = students_query.count()
        print(f"   Section {section.name}: {student_count} students")
        
        section_data = {
            "id": section.id,
            "name": section.name,
            "academic_year": section.academic_year,
            "semester": section.semester,
            "student_count": student_count
        }
        
        if include_students:
            students = students_query.all()
            print(f"   Fetched {len(students)} students for section {section.name}")
            section_data["students"] = [
                {
                    "id": student.id,
                    "student_id": student.student_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email
                }
                for student in students
            ]
            print(f"   Added {len(section_data['students'])} students to response")
        
        result.append(section_data)
    
    print(f"🎯 Returning {len(result)} sections with students included")
    return result