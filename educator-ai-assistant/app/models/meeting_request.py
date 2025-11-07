"""
Meeting request model for approval workflow
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class RequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"

class MeetingRequest(Base):
    __tablename__ = "meeting_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Meeting details
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)  # Created after approval
    requester_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    
    # Request info
    title = Column(String(200), nullable=False)
    description = Column(Text)
    requested_start = Column(DateTime(timezone=True), nullable=False)
    requested_end = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(200))
    
    # Status tracking
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    response_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True))
    
    # Relationships
    requester = relationship("Educator", foreign_keys=[requester_id])
    participant = relationship("Educator", foreign_keys=[participant_id])
    schedule = relationship("Schedule", back_populates="meeting_request")
    
    def to_dict(self):
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "requester_id": self.requester_id,
            "participant_id": self.participant_id,
            "title": self.title,
            "description": self.description,
            "requested_start": self.requested_start.isoformat() if self.requested_start else None,
            "requested_end": self.requested_end.isoformat() if self.requested_end else None,
            "location": self.location,
            "status": self.status.value if self.status else None,
            "response_message": self.response_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "requester": {
                "id": self.requester.id,
                "name": self.requester.full_name,
                "email": self.requester.email
            } if self.requester else None,
            "participant": {
                "id": self.participant.id,
                "name": self.participant.full_name,
                "email": self.participant.email
            } if self.participant else None
        }