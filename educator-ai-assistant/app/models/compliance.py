"""
Compliance model for managing compliance reports and regulatory requirements
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ComplianceType(enum.Enum):
    ATTENDANCE_REPORT = "attendance_report"
    GRADE_DISTRIBUTION = "grade_distribution"
    COURSE_EVALUATION_SUMMARY = "course_evaluation_summary"
    FACULTY_ACTIVITY_REPORT = "faculty_activity_report"
    STUDENT_PROGRESS_REPORT = "student_progress_report"
    ACCESSIBILITY_COMPLIANCE = "accessibility_compliance"
    SAFETY_REPORT = "safety_report"
    ACCREDITATION_REPORT = "accreditation_report"
    FINANCIAL_REPORT = "financial_report"
    OTHER = "other"

class ComplianceStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    OVERDUE = "overdue"

class ComplianceReport(Base):
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    
    # Report details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    compliance_type = Column(Enum(ComplianceType), nullable=False)
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.NOT_STARTED)
    
    # Regulatory information
    regulatory_body = Column(String(100))  # University, State, Federal agency
    regulation_reference = Column(String(100))  # Regulation or policy reference
    compliance_period_start = Column(DateTime(timezone=True))
    compliance_period_end = Column(DateTime(timezone=True))
    
    # Deadlines
    due_date = Column(DateTime(timezone=True), nullable=False)
    reminder_dates = Column(Text)  # JSON array of reminder dates
    submission_date = Column(DateTime(timezone=True))
    
    # Report content
    report_data = Column(Text)  # JSON string for flexible report data
    auto_generated_content = Column(Text)  # AI-generated report content
    manual_additions = Column(Text)  # Manual additions by educator
    attachments = Column(Text)  # JSON array of file attachments
    
    # Validation and review
    validation_rules = Column(Text)  # JSON string for validation criteria
    validation_status = Column(String(20), default="pending")  # pending, passed, failed
    validation_errors = Column(Text)  # JSON array of validation errors
    reviewer_comments = Column(Text)
    
    # Submission tracking
    submission_method = Column(String(50))  # email, portal, manual
    confirmation_number = Column(String(100))
    acknowledgment_received = Column(Boolean, default=False)
    
    # Automation settings
    auto_generation_enabled = Column(Boolean, default=True)
    auto_submission_enabled = Column(Boolean, default=False)
    notification_preferences = Column(Text)  # JSON string for notification settings
    
    # Integration
    external_system_id = Column(String(100))
    submission_portal_url = Column(String(500))
    api_endpoint = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_auto_update = Column(DateTime(timezone=True))
    
    # Relationships
    educator = relationship("Educator", back_populates="compliance_reports")
    
    def __repr__(self):
        return f"<ComplianceReport(id={self.id}, title='{self.title}', type='{self.compliance_type}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "educator_id": self.educator_id,
            "title": self.title,
            "description": self.description,
            "compliance_type": self.compliance_type.value if self.compliance_type else None,
            "status": self.status.value if self.status else None,
            "regulatory_body": self.regulatory_body,
            "regulation_reference": self.regulation_reference,
            "compliance_period_start": self.compliance_period_start.isoformat() if self.compliance_period_start else None,
            "compliance_period_end": self.compliance_period_end.isoformat() if self.compliance_period_end else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "validation_status": self.validation_status,
            "auto_generation_enabled": self.auto_generation_enabled,
            "auto_submission_enabled": self.auto_submission_enabled,
            "acknowledgment_received": self.acknowledgment_received,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_overdue(self):
        """Check if the report is overdue"""
        from datetime import datetime
        return self.due_date < datetime.utcnow() and self.status not in [ComplianceStatus.SUBMITTED, ComplianceStatus.APPROVED]
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        from datetime import datetime
        if self.due_date:
            delta = self.due_date - datetime.utcnow()
            return delta.days
        return None