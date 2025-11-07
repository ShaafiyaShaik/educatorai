"""
Schedule model for managing educator schedules and events
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class EventType(enum.Enum):
    CLASS = "class"
    MEETING = "meeting"
    OFFICE_HOURS = "office_hours"
    CONFERENCE = "conference"
    DEADLINE = "deadline"
    EXAM = "exam"
    WORKSHOP = "workshop"
    TASK = "task"
    OTHER = "other"

class EventStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    
    # Event details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(Enum(EventType), nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED)
    
    # Timing
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100))  # daily, weekly, monthly, etc.
    recurrence_end_date = Column(DateTime(timezone=True))
    
    # Location and participants
    location = Column(String(200))
    virtual_meeting_link = Column(String(500))
    participants = Column(Text)  # JSON string for participant list
    max_participants = Column(Integer)
    
    # Additional information
    preparation_notes = Column(Text)
    materials_needed = Column(Text)
    reminder_settings = Column(Text)  # JSON string for reminder preferences
    
    # Integration with university systems
    external_event_id = Column(String(100))  # For syncing with university calendar
    course_code = Column(String(20))
    semester = Column(String(20))
    academic_year = Column(String(10))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    educator = relationship("Educator", back_populates="schedules")
    meeting_request = relationship("MeetingRequest", back_populates="schedule", uselist=False)
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, title='{self.title}', educator_id={self.educator_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "educator_id": self.educator_id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type.value if self.event_type else None,
            "status": self.status.value if self.status else None,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "location": self.location,
            "virtual_meeting_link": self.virtual_meeting_link,
            "course_code": self.course_code,
            "semester": self.semester,
            "academic_year": self.academic_year,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }