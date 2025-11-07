"""
Message model for student-educator communication
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    receiver_type = Column(String(20), default="student")  # student, parent
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default="general")  # general, academic, behavioral, attendance
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sender = relationship("Educator", foreign_keys=[sender_id])
    receiver = relationship("Student", foreign_keys=[receiver_id])

class MessageTemplate(Base):
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    template_name = Column(String(100), nullable=False)
    subject_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    message_type = Column(String(50), default="general")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    educator = relationship("Educator")