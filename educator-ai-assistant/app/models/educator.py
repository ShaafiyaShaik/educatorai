"""
Educator model for the administrative assistant system
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Educator(Base):
    __tablename__ = "educators"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=True)
    department = Column(String(100))
    title = Column(String(100))  # Professor, Associate Professor, etc.
    office_location = Column(String(100))
    phone = Column(String(20))
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Preferences
    notification_preferences = Column(Text)  # JSON string for notification settings
    timezone = Column(String(50), default="UTC")
    communication_preferences = Column(Text)  # JSON string for communication settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    schedules = relationship("Schedule", back_populates="educator")
    records = relationship("Record", back_populates="educator")
    compliance_reports = relationship("ComplianceReport", back_populates="educator")
    sections = relationship("Section", back_populates="educator")
    sent_reports = relationship("SentReport", back_populates="educator", lazy="dynamic")
    organized_meetings = relationship("Meeting", back_populates="organizer")
    
    def __repr__(self):
        return f"<Educator(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "employee_id": self.employee_id,
            "department": self.department,
            "title": self.title,
            "office_location": self.office_location,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }