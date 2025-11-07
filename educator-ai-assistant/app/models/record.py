"""
Record model for managing educational records and administrative data
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class RecordType(enum.Enum):
    ATTENDANCE = "attendance"
    GRADE = "grade"
    ASSIGNMENT = "assignment"
    COURSE_EVALUATION = "course_evaluation"
    STUDENT_PROGRESS = "student_progress"
    MEETING_MINUTES = "meeting_minutes"
    INCIDENT_REPORT = "incident_report"
    COMMUNICATION_LOG = "communication_log"
    OTHER = "other"

class RecordStatus(enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Record(Base):
    __tablename__ = "records"
    
    id = Column(Integer, primary_key=True, index=True)
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    
    # Record details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    record_type = Column(Enum(RecordType), nullable=False)
    status = Column(Enum(RecordStatus), default=RecordStatus.DRAFT)
    
    # Academic context
    course_code = Column(String(20))
    course_name = Column(String(200))
    semester = Column(String(20))
    academic_year = Column(String(10))
    student_id = Column(String(50))  # For student-specific records
    student_name = Column(String(200))
    
    # Record data
    record_data = Column(Text)  # JSON string for flexible data storage
    grade_value = Column(Float)  # For grade records
    attendance_date = Column(DateTime(timezone=True))  # For attendance records
    
    # File attachments
    file_path = Column(String(500))
    file_type = Column(String(50))
    file_size = Column(Integer)
    
    # Metadata
    tags = Column(Text)  # JSON array of tags for categorization
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    confidentiality_level = Column(String(20), default="internal")  # public, internal, confidential, restricted
    
    # Workflow
    submitted_by = Column(String(200))
    reviewed_by = Column(String(200))
    approved_by = Column(String(200))
    review_notes = Column(Text)
    
    # Integration
    external_system_id = Column(String(100))
    sync_status = Column(String(20), default="pending")  # pending, synced, failed
    last_sync_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True))
    
    # Relationships
    educator = relationship("Educator", back_populates="records")
    
    def __repr__(self):
        return f"<Record(id={self.id}, title='{self.title}', type='{self.record_type}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "educator_id": self.educator_id,
            "title": self.title,
            "description": self.description,
            "record_type": self.record_type.value if self.record_type else None,
            "status": self.status.value if self.status else None,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "semester": self.semester,
            "academic_year": self.academic_year,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "grade_value": self.grade_value,
            "attendance_date": self.attendance_date.isoformat() if self.attendance_date else None,
            "priority": self.priority,
            "confidentiality_level": self.confidentiality_level,
            "sync_status": self.sync_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }