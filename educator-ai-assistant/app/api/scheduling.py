"""
Scheduling API endpoints for managing educator schedules and tasks
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.schedule import Schedule, EventType, EventStatus
from app.models.student import Section, Student
import enum
import json

router = APIRouter()

class TaskType(str, enum.Enum):
    MEETING_TEACHERS = "meeting_teachers"
    PARENT_TEACHER_MEETING = "parent_teacher_meeting"
    STUDENT_REVIEW = "student_review"
    PERSONAL_REMINDER = "personal_reminder"
    EXAM_SCHEDULE = "exam_schedule"

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    task_type: Optional[TaskType] = TaskType.PERSONAL_REMINDER
    start_datetime: datetime
    end_datetime: datetime
    location: Optional[str] = ""
    priority: Optional[str] = "medium"
    send_notifications: Optional[bool] = True
    
    # Additional fields that might come from frontend
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    participants: Optional[List[Dict[str, Any]]] = []
    
    # Meeting scheduler integration fields
    meeting_type: Optional[str] = None  # 'section' or 'individual'
    section_id: Optional[int] = None
    student_ids: Optional[List[int]] = []
    send_immediately: Optional[bool] = True
    scheduled_send_at: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    task_type: str
    status: str
    start: str
    end: str
    location: Optional[str] = None
    priority: str = "medium"
    participants: List[Dict[str, Any]] = []
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/tasks/conflicts")
async def check_task_conflicts(
    scheduled_date: str,
    scheduled_time: str,
    duration_minutes: int = 60,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Check for scheduling conflicts"""
    
    try:
        # Parse the date and time
        start_datetime = datetime.fromisoformat(f"{scheduled_date}T{scheduled_time}")
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Check for conflicts
        conflicts = db.query(Schedule).filter(
            Schedule.educator_id == current_educator.id,
            Schedule.status != EventStatus.CANCELLED,
            Schedule.start_datetime < end_datetime,
            Schedule.end_datetime > start_datetime
        ).all()
        
        conflict_tasks = []
        for conflict in conflicts:
            conflict_tasks.append({
                "id": conflict.id,
                "title": conflict.title,
                "start": conflict.start_datetime.isoformat(),
                "end": conflict.end_datetime.isoformat(),
                "type": conflict.event_type.value
            })
        
        return {
            "has_conflict": len(conflict_tasks) > 0,
            "conflicts": conflict_tasks,
            "suggested_times": []  # Could implement logic for alternative times
        }
        
    except Exception as e:
        print(f"Error checking conflicts: {str(e)}")
        return {
            "has_conflict": False,
            "conflicts": [],
            "suggested_times": []
        }

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskRequest,
    background_tasks: BackgroundTasks,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create a new task/meeting"""
    
    print(f"📝 Received task data: {task_data}")
    print(f"   Task type: {task_data.task_type}")
    print(f"   Start: {task_data.start_datetime}")
    print(f"   End: {task_data.end_datetime}")
    print(f"   Meeting type: {task_data.meeting_type}")
    print(f"   Section ID: {task_data.section_id}")
    print(f"   Student IDs: {task_data.student_ids}")
    
    try:
        # Build participants JSON
        participants = {}
        
        if task_data.meeting_type == 'section' and task_data.section_id:
            # Section-based task
            participants['sections'] = [task_data.section_id]
            print(f"   📚 Task targeted to section {task_data.section_id}")
            
        elif task_data.meeting_type == 'individual' and task_data.student_ids:
            # Individual students task
            # Get student emails for participants
            students = db.query(Student).filter(Student.id.in_(task_data.student_ids)).all()
            student_emails = [student.email for student in students]
            participants['students'] = student_emails
            print(f"   👥 Task targeted to individual students: {student_emails}")
        
        # Create the schedule event
        db_schedule = Schedule(
            educator_id=current_educator.id,
            title=task_data.title,
            description=task_data.description,
            event_type=EventType.TASK,
            start_datetime=task_data.start_datetime,
            end_datetime=task_data.end_datetime,
            location=task_data.location,
            status=EventStatus.SCHEDULED,
            participants=json.dumps(participants) if participants else None
        )
        
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        print(f"   ✅ Task created with ID {db_schedule.id}")
        print(f"   📋 Participants: {participants}")
        
        # Format response
        response_data = {
            "id": db_schedule.id,
            "title": db_schedule.title,
            "description": task_data.description or "",
            "task_type": task_data.task_type.value if task_data.task_type else "personal_reminder",
            "status": db_schedule.status.value,
            "start": db_schedule.start_datetime.isoformat(),
            "end": db_schedule.end_datetime.isoformat(),
            "location": db_schedule.location or "",
            "priority": task_data.priority,
            "participants": participants,
            "created_at": datetime.now().isoformat()
        }
        
        return TaskResponse(**response_data)

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating task: {str(e)}"
        )

@router.post("/tasks/simple")
async def create_simple_task(
    request_data: dict,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create a task with flexible input format"""
    
    print(f"📝 Received simple task data: {request_data}")
    
    try:
        # Extract data with fallbacks
        title = request_data.get("title", "Untitled Task")
        description = request_data.get("description", "")
        location = request_data.get("location", "")
        task_type = request_data.get("task_type", "personal_reminder")
        
        # Handle datetime parsing
        if "start_datetime" in request_data:
            start_dt = datetime.fromisoformat(request_data["start_datetime"].replace("Z", ""))
        elif "scheduled_date" in request_data and "scheduled_time" in request_data:
            start_dt = datetime.fromisoformat(f"{request_data['scheduled_date']}T{request_data['scheduled_time']}")
        else:
            start_dt = datetime.now() + timedelta(hours=1)
        
        # Handle end datetime
        if "end_datetime" in request_data:
            end_dt = datetime.fromisoformat(request_data["end_datetime"].replace("Z", ""))
        elif "duration_minutes" in request_data:
            duration = int(request_data["duration_minutes"])
            end_dt = start_dt + timedelta(minutes=duration)
        else:
            end_dt = start_dt + timedelta(hours=1)
        
        # Create the schedule event
        db_schedule = Schedule(
            educator_id=current_educator.id,
            title=title,
            description=description,
            event_type=EventType.TASK,
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=location,
            status=EventStatus.SCHEDULED
        )
        
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        # Format response
        return {
            "id": db_schedule.id,
            "title": db_schedule.title,
            "description": db_schedule.description,
            "task_type": task_type,
            "status": db_schedule.status.value,
            "start": db_schedule.start_datetime.isoformat(),
            "end": db_schedule.end_datetime.isoformat(),
            "location": db_schedule.location or "",
            "priority": "medium",
            "participants": [],
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating simple task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating task: {str(e)}"
        )

@router.get("/tasks")
async def get_tasks(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all tasks for the current educator"""
    
    try:
        schedules = db.query(Schedule).filter(
            Schedule.educator_id == current_educator.id,
            Schedule.event_type == EventType.TASK
        ).order_by(Schedule.start_datetime.desc()).all()
        
        tasks = []
        for schedule in schedules:
            # Parse participants if stored as JSON string
            participants = []
            if schedule.participants:
                try:
                    import json
                    participants = json.loads(schedule.participants)
                except:
                    participants = []
            
            # Calculate duration in minutes
            duration_minutes = 60  # default
            if schedule.end_datetime and schedule.start_datetime:
                duration_delta = schedule.end_datetime - schedule.start_datetime
                duration_minutes = int(duration_delta.total_seconds() / 60)
            
            # Format the task data for frontend
            task_data = {
                "id": schedule.id,
                "title": schedule.title,
                "description": schedule.description or "",
                "task_type": "task",  # Map event_type to task_type
                "scheduled_date": schedule.start_datetime.date().isoformat(),
                "scheduled_time": schedule.start_datetime.time().strftime("%H:%M"),
                "duration_minutes": duration_minutes,
                "location": schedule.location or "",
                "status": schedule.status.value,
                "participants": participants,
                "is_completed": schedule.status == EventStatus.COMPLETED,
                "priority": "medium",  # default priority
                "preparation_notes": schedule.preparation_notes or "",
                "materials_needed": schedule.materials_needed or "",
                # Keep legacy fields for compatibility
                "start": schedule.start_datetime.isoformat(),
                "end": schedule.end_datetime.isoformat(),
                "created_at": schedule.created_at.isoformat() if schedule.created_at else None
            }
            
            tasks.append(task_data)
        
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tasks: {str(e)}"
        )

@router.get("/calendar")
async def get_calendar_view(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get calendar view with all events and tasks"""
    
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)
    
    day_start = datetime.combine(start_date, time.min)
    day_end = datetime.combine(end_date, time.max)
    
    all_schedules = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.start_datetime >= day_start,
        Schedule.start_datetime <= day_end
    ).order_by(Schedule.start_datetime).all()
    
    calendar_events = []
    for schedule in all_schedules:
        # Extract local date for calendar display (avoid timezone issues)
        local_date = schedule.start_datetime.date().isoformat()
        
        event_data = {
            "id": schedule.id,
            "title": schedule.title,
            "start": schedule.start_datetime.isoformat(),
            "end": schedule.end_datetime.isoformat(),
            "start_datetime": schedule.start_datetime.isoformat(),
            "end_datetime": schedule.end_datetime.isoformat(),
            "local_date": local_date,  # Add explicit local date for calendar
            "location": schedule.location or "",
            "type": schedule.event_type.value,
            "status": schedule.status.value,
            "description": schedule.description or "",
            "participants": []
        }
        
        calendar_events.append(event_data)
    
    return {"events": calendar_events, "total": len(calendar_events)}

@router.get("/sections/{section_id}/students")
async def get_section_students_for_scheduling(
    section_id: int,
    criteria: Optional[str] = "all",
    count: Optional[int] = None,
    range_start: Optional[int] = None,
    range_end: Optional[int] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get students from a section for scheduling purposes with range selection"""
    
    # Verify section belongs to educator
    section = db.query(Section).filter(
        Section.id == section_id,
        Section.educator_id == current_educator.id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Get students
    students_query = db.query(Student).filter(Student.section_id == section_id)
    students = students_query.all()
    
    # Apply range selection if requested (e.g., roll numbers 10-15)
    if criteria == "range" and range_start and range_end:
        filtered_students = []
        for student in students:
            try:
                roll_num = int(student.student_id.lstrip('0')) if student.student_id else 0
                if range_start <= roll_num <= range_end:
                    filtered_students.append(student)
            except (ValueError, AttributeError):
                continue
        students = filtered_students
    
    # Apply count limit
    if count:
        students = students[:count]
    
    students_data = []
    for student in students:
        try:
            roll_number = int(student.student_id.lstrip('0')) if student.student_id else 0
        except (ValueError, AttributeError):
            roll_number = 0
        
        students_data.append({
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "email": student.email,
            "student_id": student.student_id,
            "roll_number": roll_number
        })
    
    return {
        "section_id": section_id,
        "section_name": section.name,
        "criteria": criteria,
        "range_start": range_start,
        "range_end": range_end,
        "total_count": len(students_data),
        "students": students_data
    }

@router.get("/")
async def get_schedules(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all schedules for the current educator"""
    
    schedules = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id
    ).order_by(Schedule.start_datetime.desc()).all()
    
    return {"schedules": schedules, "total": len(schedules)}