"""
Communication model for tracking emails and notifications
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_email = Column(String(100), nullable=False)
    recipient_email = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")  # sent, pending, failed
    email_type = Column(String(50), default="email")  # email, notification, bulk_email
    
    def __repr__(self):
        return f"<Communication(id={self.id}, from={self.sender_email}, to={self.recipient_email}, subject='{self.subject}')>"