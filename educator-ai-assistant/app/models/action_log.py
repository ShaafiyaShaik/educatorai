"""Action log model for recording automated actions performed by the chatbot.

Records actor (educator), action type, target object and an optional JSON
payload. Includes an `undone` flag for actions that were later reversed.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ActionLog(Base):
    __tablename__ = "action_log"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("educators.id"), nullable=True)
    action_type = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    payload = Column(Text, nullable=True)  # JSON string
    undone = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    undone_at = Column(DateTime(timezone=True), nullable=True)

    actor = relationship("Educator")

    def to_dict(self):
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "action_type": self.action_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "payload": self.payload,
            "undone": self.undone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "undone_at": self.undone_at.isoformat() if self.undone_at else None,
        }
