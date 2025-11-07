"""
Enhanced scheduling API with meeting requests and approval workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.schedule import Schedule, EventType, EventStatus
from app.models.meeting_request import MeetingRequest, RequestStatus
from datetime import datetime, date, timedelta
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class MeetingRequestCreate(BaseModel):
    participant_ids: List[int]
    title: str
    description: Optional[str] = None
    requested_start: datetime
    requested_end: datetime
    location: Optional[str] = None

class MeetingRequestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    requested_start: str
    requested_end: str
    location: Optional[str]
    status: str
    requester_name: str
    requester_email: str
    created_at: str

class MeetingRequestAction(BaseModel):
    action: str  # "approve" or "decline"
    response_message: Optional[str] = None

@router.post("/meeting-requests", response_model=dict)
async def create_meeting_request(
    request_data: MeetingRequestCreate,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create meeting requests for multiple participants"""
    
    # Check for conflicts in requester's schedule
    conflicts = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.start_datetime < request_data.requested_end,
        Schedule.end_datetime > request_data.requested_start
    ).all()
    
    if conflicts:
        conflict_details = [f'"{c.title}" at {c.start_datetime.strftime("%Y-%m-%d %H:%M")}' for c in conflicts]
        raise HTTPException(
            status_code=400,
            detail=f"You have scheduling conflicts: {', '.join(conflict_details)}"
        )
    
    # Verify participants exist
    participants = db.query(Educator).filter(Educator.id.in_(request_data.participant_ids)).all()
    if len(participants) != len(request_data.participant_ids):
        raise HTTPException(status_code=400, detail="One or more participants not found")
    
    # Create meeting requests for each participant
    created_requests = []
    for participant in participants:
        # Skip self
        if participant.id == current_educator.id:
            continue
            
        # Check for participant conflicts
        participant_conflicts = db.query(Schedule).filter(
            Schedule.educator_id == participant.id,
            Schedule.start_datetime < request_data.requested_end,
            Schedule.end_datetime > request_data.requested_start
        ).all()
        
        meeting_request = MeetingRequest(
            requester_id=current_educator.id,
            participant_id=participant.id,
            title=request_data.title,
            description=request_data.description,
            requested_start=request_data.requested_start,
            requested_end=request_data.requested_end,
            location=request_data.location,
            status=RequestStatus.PENDING
        )
        
        db.add(meeting_request)
        db.commit()
        db.refresh(meeting_request)
        created_requests.append(meeting_request.to_dict())
        
        # TODO: Send notification to participant
        # await send_meeting_request_notification(participant, meeting_request)
    
    return {
        "message": f"Meeting requests sent to {len(created_requests)} participants",
        "requests": created_requests,
        "conflicts_found": len([p for p in participants if participant_conflicts])
    }

@router.get("/meeting-requests/incoming", response_model=List[MeetingRequestResponse])
async def get_incoming_requests(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get meeting requests for current user"""
    requests = db.query(MeetingRequest).filter(
        MeetingRequest.participant_id == current_educator.id,
        MeetingRequest.status == RequestStatus.PENDING
    ).all()
    
    return [
        MeetingRequestResponse(
            id=req.id,
            title=req.title,
            description=req.description,
            requested_start=req.requested_start.isoformat(),
            requested_end=req.requested_end.isoformat(),
            location=req.location,
            status=req.status.value,
            requester_name=req.requester.full_name,
            requester_email=req.requester.email,
            created_at=req.created_at.isoformat()
        ) for req in requests
    ]

@router.get("/meeting-requests/outgoing")
async def get_outgoing_requests(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get meeting requests sent by current user"""
    requests = db.query(MeetingRequest).filter(
        MeetingRequest.requester_id == current_educator.id
    ).all()
    
    return [req.to_dict() for req in requests]

@router.post("/meeting-requests/{request_id}/respond")
async def respond_to_meeting_request(
    request_id: int,
    action_data: MeetingRequestAction,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Approve or decline a meeting request"""
    
    meeting_request = db.query(MeetingRequest).filter(
        MeetingRequest.id == request_id,
        MeetingRequest.participant_id == current_educator.id,
        MeetingRequest.status == RequestStatus.PENDING
    ).first()
    
    if not meeting_request:
        raise HTTPException(status_code=404, detail="Meeting request not found")
    
    if action_data.action == "approve":
        # Check for conflicts again
        conflicts = db.query(Schedule).filter(
            Schedule.educator_id == current_educator.id,
            Schedule.start_datetime < meeting_request.requested_end,
            Schedule.end_datetime > meeting_request.requested_start
        ).all()
        
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail="You now have a scheduling conflict. Please contact the requester."
            )
        
        # Create schedule entries for both participants
        # Requester's schedule
        requester_schedule = Schedule(
            educator_id=meeting_request.requester_id,
            title=meeting_request.title,
            description=meeting_request.description,
            event_type=EventType.MEETING,
            start_datetime=meeting_request.requested_start,
            end_datetime=meeting_request.requested_end,
            location=meeting_request.location,
            participants=f"Meeting with {current_educator.full_name}"
        )
        
        # Participant's schedule  
        participant_schedule = Schedule(
            educator_id=current_educator.id,
            title=meeting_request.title,
            description=meeting_request.description,
            event_type=EventType.MEETING,
            start_datetime=meeting_request.requested_start,
            end_datetime=meeting_request.requested_end,
            location=meeting_request.location,
            participants=f"Meeting with {meeting_request.requester.full_name}"
        )
        
        db.add(requester_schedule)
        db.add(participant_schedule)
        
        meeting_request.status = RequestStatus.APPROVED
        meeting_request.schedule_id = requester_schedule.id
        
    elif action_data.action == "decline":
        meeting_request.status = RequestStatus.DECLINED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    meeting_request.response_message = action_data.response_message
    meeting_request.responded_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: Send notification to requester
    # await send_meeting_response_notification(meeting_request)
    
    return {
        "message": f"Meeting request {action_data.action}d successfully",
        "request": meeting_request.to_dict()
    }

@router.get("/conflicts")
async def check_schedule_conflicts(
    start_time: datetime,
    end_time: datetime,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Check for scheduling conflicts for current user"""
    
    conflicts = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.start_datetime < end_time,
        Schedule.end_datetime > start_time
    ).all()
    
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": [
            {
                "id": conflict.id,
                "title": conflict.title,
                "start": conflict.start_datetime.isoformat(),
                "end": conflict.end_datetime.isoformat(),
                "location": conflict.location
            } for conflict in conflicts
        ]
    }