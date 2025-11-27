from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models import ActionLog
from app.models.message import Message
from app.models.meeting_schedule import Meeting

router = APIRouter()


@router.post("/{action_id}/undo")
async def undo_action(action_id: int, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    """Undo a recent action recorded in the ActionLog.

    Supports undo for messages and meetings within a short timeframe.
    """
    log = db.query(ActionLog).filter(ActionLog.id == action_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    if log.undone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action already undone")

    # Basic undo window (configurable later)
    undo_window_seconds = 300  # 5 minutes
    now = datetime.utcnow()
    if log.created_at and (now - log.created_at) > timedelta(seconds=undo_window_seconds):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Undo window expired")

    # Handle message undo
    if log.action_type == "send_message" and log.target_type == "message" and log.target_id:
        message = db.query(Message).filter(Message.id == log.target_id).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        # Only sender may undo
        if message.sender_id != current_educator.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to undo this message")

        # delete message
        db.delete(message)
        log.undone = True
        log.undone_at = datetime.utcnow()
        db.add(log)
        db.commit()
        return {"status": "ok", "detail": "Message undone"}

    # Handle meeting undo
    if log.action_type == "schedule_meeting" and log.target_type == "meeting" and log.target_id:
        meeting = db.query(Meeting).filter(Meeting.id == log.target_id).first()
        if not meeting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        if meeting.organizer_id != current_educator.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to undo this meeting")
        # Only allow undo within window
        db.delete(meeting)
        log.undone = True
        log.undone_at = datetime.utcnow()
        db.add(log)
        db.commit()
        return {"status": "ok", "detail": "Meeting undone"}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Undo not supported for this action type")


@router.get("/")
async def list_actions(skip: int = 0, limit: int = 50, undone: Optional[bool] = None, current_educator=Depends(get_current_educator), db: Session = Depends(get_db)):
    """List recent action logs for the current educator.

    Filters by the current educator's id. Admin users may expand this later.
    """
    query = db.query(ActionLog).filter(ActionLog.actor_id == current_educator.id)
    if undone is not None:
        query = query.filter(ActionLog.undone == bool(undone))
    total = query.count()
    items = query.order_by(ActionLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [i.to_dict() for i in items]}
