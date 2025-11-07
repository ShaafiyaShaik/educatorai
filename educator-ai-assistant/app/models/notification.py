"""
Notification model for the Teacher Portal
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class NotificationType(enum.Enum):
    GRADE_REPORT = "grade_report"
    SECTION_SUMMARY = "section_summary"
    ANNOUNCEMENT = "announcement"
    REMINDER = "reminder"
    COMMUNICATION = "communication"

class NotificationStatus(enum.Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipients
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=True)  # For teacher notifications
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)    # For student notifications
    
    # Notification content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    
    # Additional data (JSON string for flexibility)
    additional_data = Column(Text)  # For storing additional structured data
    
    # Priority and categorization
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    category = Column(String(50))  # academic, administrative, personal, etc.
    
    # Scheduling
    scheduled_for = Column(DateTime(timezone=True))  # For scheduled notifications
    expires_at = Column(DateTime(timezone=True))     # For time-sensitive notifications
    
    # Tracking
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    educator = relationship("Educator", foreign_keys=[educator_id])
    student = relationship("Student", foreign_keys=[student_id])
    
    def __repr__(self):
        recipient = f"educator_{self.educator_id}" if self.educator_id else f"student_{self.student_id}"
        return f"<Notification(id={self.id}, type='{self.notification_type.value}', recipient='{recipient}')>"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.status = NotificationStatus.READ
        self.read_at = func.now()
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type.value if self.notification_type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "additional_data": self.additional_data
        }