"""
Report model for tracking sent performance reports
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ReportType(enum.Enum):
    INDIVIDUAL_STUDENT = "individual_student"
    SECTION_SUMMARY = "section_summary"
    SUBJECT_ANALYSIS = "subject_analysis"
    OVERALL_PERFORMANCE = "overall_performance"

class RecipientType(enum.Enum):
    STUDENT = "student"
    PARENT = "parent"
    BOTH = "both"

class ReportStatus(enum.Enum):
    SENT = "sent"
    VIEWED = "viewed"
    ARCHIVED = "archived"

class SentReport(Base):
    __tablename__ = "sent_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Report identification
    report_type = Column(Enum(ReportType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Sender information
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    
    # Recipients
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)  # For individual reports
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)  # For section reports
    recipient_type = Column(Enum(RecipientType), nullable=False)
    
    # Report content and metadata
    report_data = Column(JSON)  # Stores the actual report data
    report_file_path = Column(String(500))  # Path to generated PDF/Excel file
    report_format = Column(String(20), default="pdf")  # pdf, excel, both
    
    # Status tracking
    status = Column(Enum(ReportStatus), default=ReportStatus.SENT)
    is_viewed_by_student = Column(Boolean, default=False)
    is_viewed_by_parent = Column(Boolean, default=False)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    viewed_at = Column(DateTime(timezone=True))
    student_viewed_at = Column(DateTime(timezone=True))
    parent_viewed_at = Column(DateTime(timezone=True))
    
    # Additional metadata
    academic_year = Column(String(20), default="2024-2025")
    semester = Column(String(20))
    comments = Column(Text)  # Additional comments from teacher
    
    # Relationships
    educator = relationship("Educator", back_populates="sent_reports")
    student = relationship("Student", back_populates="received_reports")
    section = relationship("Section", back_populates="section_reports")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def mark_as_viewed(self, viewer_type: str):
        """Mark report as viewed by student or parent"""
        now = func.now()
        if viewer_type == "student":
            self.is_viewed_by_student = True
            self.student_viewed_at = now
        elif viewer_type == "parent":
            self.is_viewed_by_parent = True
            self.parent_viewed_at = now
        
        # Update overall status if both have viewed (for 'both' recipient type)
        if self.recipient_type == RecipientType.BOTH:
            if self.is_viewed_by_student and self.is_viewed_by_parent:
                self.status = ReportStatus.VIEWED
                self.viewed_at = now
        else:
            self.status = ReportStatus.VIEWED
            self.viewed_at = now
    
    def __repr__(self):
        return f"<SentReport(id={self.id}, type='{self.report_type}', title='{self.title}')>"