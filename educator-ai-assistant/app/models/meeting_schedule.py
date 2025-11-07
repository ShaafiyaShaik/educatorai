"""
Meeting scheduling models for teacher-initiated meetings with students/parents
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class MeetingType(enum.Enum):
    SECTION = "section"
    INDIVIDUAL = "individual"
    CUSTOM = "custom"

class RecipientType(enum.Enum):
    STUDENT = "student"
    PARENT = "parent"

class DeliveryStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class RSVPStatus(enum.Enum):
    NO_RESPONSE = "no_response"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"

class Meeting(Base):
    """Canonical meeting record created by teachers"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Meeting organizer
    organizer_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    
    # Meeting details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    meeting_date = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer, default=60)
    location = Column(String(200))
    virtual_meeting_link = Column(String(500))
    
    # Meeting configuration
    meeting_type = Column(Enum(MeetingType), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)  # Only if section meeting
    notify_parents = Column(Boolean, default=True)
    requires_rsvp = Column(Boolean, default=False)
    send_reminders = Column(Boolean, default=True)
    reminder_minutes_before = Column(Integer, default=60)
    
    # Scheduling
    send_immediately = Column(Boolean, default=True)
    scheduled_send_at = Column(DateTime(timezone=True), nullable=True)
    
    # Attachments (JSON array of file URLs/paths)
    attachments = Column(JSON, default=list)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organizer = relationship("Educator", back_populates="organized_meetings")
    section = relationship("Section", back_populates="meetings")
    recipients = relationship("MeetingRecipient", back_populates="meeting", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "organizer_id": self.organizer_id,
            "title": self.title,
            "description": self.description,
            "meeting_date": self.meeting_date.isoformat() if self.meeting_date else None,
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "virtual_meeting_link": self.virtual_meeting_link,
            "meeting_type": self.meeting_type.value if self.meeting_type else None,
            "section_id": self.section_id,
            "notify_parents": self.notify_parents,
            "requires_rsvp": self.requires_rsvp,
            "send_reminders": self.send_reminders,
            "reminder_minutes_before": self.reminder_minutes_before,
            "send_immediately": self.send_immediately,
            "scheduled_send_at": self.scheduled_send_at.isoformat() if self.scheduled_send_at else None,
            "attachments": self.attachments,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "organizer": self.organizer.to_dict() if self.organizer else None,
            "section": self.section.to_dict() if self.section else None,
            "recipient_count": len(self.recipients) if self.recipients else 0
        }

class MeetingRecipient(Base):
    """Per-recipient delivery entries for meeting notifications"""
    __tablename__ = "meeting_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    recipient_id = Column(Integer, nullable=False)  # Student or Parent ID
    recipient_type = Column(Enum(RecipientType), nullable=False)
    
    # Delivery status
    delivery_status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    rsvp_status = Column(Enum(RSVPStatus), default=RSVPStatus.NO_RESPONSE)
    
    # Delivery methods used (JSON array)
    delivery_methods = Column(JSON, default=["in_app"])  # ["in_app", "email", "push"]
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    rsvp_at = Column(DateTime(timezone=True), nullable=True)
    
    # Response message from recipient
    rsvp_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    meeting = relationship("Meeting", back_populates="recipients")
    
    def to_dict(self):
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "recipient_id": self.recipient_id,
            "recipient_type": self.recipient_type.value if self.recipient_type else None,
            "delivery_status": self.delivery_status.value if self.delivery_status else None,
            "rsvp_status": self.rsvp_status.value if self.rsvp_status else None,
            "delivery_methods": self.delivery_methods,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "rsvp_at": self.rsvp_at.isoformat() if self.rsvp_at else None,
            "rsvp_message": self.rsvp_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }