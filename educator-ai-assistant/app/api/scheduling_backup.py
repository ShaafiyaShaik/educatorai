"""
Enhanced Scheduling API endpoints for managing educator schedules, tasks, and meetings with participants
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel, validator
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.schedule import Schedule, EventType, EventStatus
from app.models.student import Section, Student
from app.services.email_service import EmailService
import enum
import json

router = APIRouter()
):
    """Create a new task/meeting with participants"""
    
    # Debug logging
    print(f"📝 Creating task: {task_data.title}")
    print(f"   Task type: {task_data.task_type}")
    print(f"   Start: {task_data.start_datetime}")
    print(f"   End: {task_data.end_datetime}")
    print(f"   Participants: {task_data.participants}")
    
    try:rom sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel, validator
from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.models.schedule import Schedule, EventType, EventStatus
from app.models.student import Section, Student
from app.services.email_service import EmailService
import enum
import json

router = APIRouter()

# Enhanced enums for task types and participant types
class TaskType(str, enum.Enum):
    MEETING_TEACHERS = "meeting_teachers"
    PARENT_TEACHER_MEETING = "parent_teacher_meeting"
    STUDENT_REVIEW = "student_review"
    PERSONAL_REMINDER = "personal_reminder"
    EXAM_SCHEDULE = "exam_schedule"

class ParticipantType(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    SECTION = "section"

class StudentSelectionCriteria(BaseModel):
    section_id: Optional[int] = None
    count: Optional[int] = None  # e.g., top 10, bottom 10
    criteria: Optional[str] = None  # "top_performers", "low_performers", "all", "random", "range"
    specific_student_ids: Optional[List[int]] = None
    # Range selection for roll numbers (e.g., 10-15)
    range_start: Optional[int] = None  # Starting roll number
    range_end: Optional[int] = None    # Ending roll number

class ParticipantRequest(BaseModel):
    type: ParticipantType
    student_selection: Optional[StudentSelectionCriteria] = None
    teacher_ids: Optional[List[int]] = None
    section_ids: Optional[List[int]] = None

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    task_type: TaskType
    start_datetime: datetime
    end_datetime: Optional[datetime] = None  # Make optional, calculate from duration if needed
    location: Optional[str] = ""
    participants: Optional[ParticipantRequest] = None
    priority: Optional[str] = "medium"  # low, medium, high
    send_notifications: Optional[bool] = True
    
    # Additional fields that might come from frontend
    date: Optional[str] = None
    time: Optional[str] = None
    duration_minutes: Optional[int] = None
    
    @validator('end_datetime', pre=True, always=True)
    def set_end_datetime(cls, v, values):
        if v is None and 'start_datetime' in values and 'duration_minutes' in values:
            if values['duration_minutes']:
                return values['start_datetime'] + timedelta(minutes=values['duration_minutes'])
        return v

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    task_type: str
    status: str
    start: str  # ISO format for frontend
    end: str    # ISO format for frontend
    location: Optional[str] = None
    priority: str = "medium"
    participants: List[Dict[str, Any]] = []
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class ConflictCheckRequest(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    exclude_event_id: Optional[int] = None

# Pydantic models
class ScheduleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str
    start_datetime: datetime
    end_datetime: datetime
    location: Optional[str] = None
    virtual_meeting_link: Optional[str] = None
    course_code: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[str] = None
    virtual_meeting_link: Optional[str] = None
    status: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_type: str
    status: str
    start_datetime: str
    end_datetime: str
    location: Optional[str]
    virtual_meeting_link: Optional[str]
    course_code: Optional[str]
    is_recurring: bool
    created_at: str

def select_students_by_criteria(
    db: Session, 
    section_id: int, 
    criteria: StudentSelectionCriteria,
    current_educator: Educator
) -> List[Student]:
    """Select students based on criteria (top performers, low performers, etc.)"""
    
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
    
    # Get base query for students in section
    students_query = db.query(Student).filter(Student.section_id == section_id)
    
    # Handle specific student IDs
    if criteria.specific_student_ids:
        students_query = students_query.filter(Student.id.in_(criteria.specific_student_ids))
        return students_query.all()
    
    # Handle range selection by roll number/student_id
    if criteria.criteria == "range" and criteria.range_start and criteria.range_end:
        # Convert string student_id to integer for comparison if needed
        # Assuming student_id is stored as string like "001", "002", etc.
        students = students_query.all()
        range_students = []
        for student in students:
            try:
                # Extract numeric part from student_id for comparison
                student_num = int(student.student_id.lstrip('0')) if student.student_id else 0
                if criteria.range_start <= student_num <= criteria.range_end:
                    range_students.append(student)
            except (ValueError, AttributeError):
                # If student_id is not numeric, skip
                continue
        return sorted(range_students, key=lambda s: int(s.student_id.lstrip('0')) if s.student_id else 0)
    
    # Get all students with their average grades for sorting
    students = students_query.all()
    
    if not students:
        return []
    
    # Calculate average grades for sorting
    students_with_avg = []
    for student in students:
        grades = [grade.grade_value for grade in student.grades if grade.grade_value]
        avg_grade = sum(grades) / len(grades) if grades else 0
        students_with_avg.append((student, avg_grade))
    
    # Sort based on criteria
    if criteria.criteria == "top_performers":
        students_with_avg.sort(key=lambda x: x[1], reverse=True)  # Highest grades first
    elif criteria.criteria == "low_performers":
        students_with_avg.sort(key=lambda x: x[1])  # Lowest grades first
    elif criteria.criteria == "random":
        import random
        random.shuffle(students_with_avg)
    # For "all" or None, keep original order
    
    # Apply count limit
    if criteria.count:
        students_with_avg = students_with_avg[:criteria.count]
    
    return [student for student, _ in students_with_avg]

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskRequest,
    background_tasks: BackgroundTasks,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create a new task/meeting with participant management"""
    
    # Check for time conflicts
    conflicts = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.status != EventStatus.CANCELLED,
        Schedule.start_datetime < task_data.end_datetime,
        Schedule.end_datetime > task_data.start_datetime
    ).all()
    
    if conflicts:
        conflict_titles = [conflict.title for conflict in conflicts]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Time conflict with existing events: {', '.join(conflict_titles)}"
        )
    
    # Create the schedule event
    db_schedule = Schedule(
        educator_id=current_educator.id,
        title=task_data.title,
        description=task_data.description,
        event_type=EventType.TASK,  # Use TASK type for our new task system
        start_datetime=task_data.start_datetime,
        end_datetime=task_data.end_datetime,
        location=task_data.location,
        status=EventStatus.SCHEDULED
    )
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    # Prepare participants data
    participants_data = []
    
    if task_data.participants:
        if task_data.participants.type == ParticipantType.STUDENT:
            # Handle student selection
            if task_data.participants.student_selection:
                selection = task_data.participants.student_selection
                
                if selection.section_id:
                    # Select students from section based on criteria
                    selected_students = select_students_by_criteria(
                        db, selection.section_id, selection, current_educator
                    )
                    
                    for student in selected_students:
                        participants_data.append({
                            "type": "student",
                            "id": student.id,
                            "name": f"{student.first_name} {student.last_name}",
                            "email": student.email,
                            "section": student.section.name
                        })
                        
        elif task_data.participants.type == ParticipantType.TEACHER:
            # Handle teacher participants
            if task_data.participants.teacher_ids:
                teachers = db.query(Educator).filter(
                    Educator.id.in_(task_data.participants.teacher_ids)
                ).all()
                
                for teacher in teachers:
                    participants_data.append({
                        "type": "teacher",
                        "id": teacher.id,
                        "name": f"{teacher.first_name} {teacher.last_name}",
                        "email": teacher.email,
                        "department": teacher.department
                    })
                    
        elif task_data.participants.type == ParticipantType.SECTION:
            # Handle entire section(s)
            if task_data.participants.section_ids:
                sections = db.query(Section).filter(
                    Section.id.in_(task_data.participants.section_ids),
                    Section.educator_id == current_educator.id
                ).all()
                
                for section in sections:
                    participants_data.append({
                        "type": "section",
                        "id": section.id,
                        "name": section.name,
                        "student_count": len(section.students)
                    })
    
    # Store participants data in the description as JSON for now
    # (In a production system, you'd want a separate participants table)
    participants_json = json.dumps(participants_data)
    db_schedule.description = f"{task_data.description or ''}\n\nParticipants: {participants_json}"
    db.commit()
    
    # Send notifications if requested
    if task_data.send_notifications and participants_data:
        background_tasks.add_task(
            send_task_notifications,
            db_schedule,
            participants_data,
            current_educator
        )
    
    # Format response
    response_data = {
        "id": db_schedule.id,
        "title": db_schedule.title,
        "description": task_data.description,
        "task_type": task_data.task_type.value,
        "status": db_schedule.status.value,
        "start": db_schedule.start_datetime.isoformat(),
        "end": db_schedule.end_datetime.isoformat(),
        "location": db_schedule.location,
        "priority": task_data.priority,
        "participants": participants_data,
        "created_at": db_schedule.created_at.isoformat() if db_schedule.created_at else datetime.now().isoformat()
    }
    
    return TaskResponse(**response_data)

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating task: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating task: {str(e)}"
        )

@router.post("/tasks/simple")
async def create_simple_task(
    title: str,
    description: str = "",
    task_type: str = "personal_reminder",
    start_datetime: str = "",
    duration_minutes: int = 60,
    location: str = "",
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Simple task creation endpoint for debugging"""
    
    try:
        # Parse datetime
        if start_datetime:
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        else:
            start_dt = datetime.now() + timedelta(hours=1)
        
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Map task type
        task_type_enum = TaskType.PERSONAL_REMINDER
        if task_type == "meeting_teachers":
            task_type_enum = TaskType.MEETING_TEACHERS
        elif task_type == "parent_teacher_meeting":
            task_type_enum = TaskType.PARENT_TEACHER_MEETING
        elif task_type == "student_review":
            task_type_enum = TaskType.STUDENT_REVIEW
        elif task_type == "exam_schedule":
            task_type_enum = TaskType.EXAM_SCHEDULE
        
        # Create schedule
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
        
        return {
            "id": db_schedule.id,
            "title": db_schedule.title,
            "description": db_schedule.description,
            "task_type": task_type,
            "status": db_schedule.status.value,
            "start": db_schedule.start_datetime.isoformat(),
            "end": db_schedule.end_datetime.isoformat(),
            "location": db_schedule.location,
            "message": "Task created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating simple task: {str(e)}"
        )

async def send_task_notifications(
    schedule: Schedule,
    participants: List[Dict],
    educator: Educator
):
    """Send notifications to task participants"""
    # This would integrate with your notification system
    # For now, we'll just log the notifications
    print(f"📧 Sending notifications for task: {schedule.title}")
    print(f"   Educator: {educator.first_name} {educator.last_name}")
    print(f"   Participants: {len(participants)} people")
    
    for participant in participants:
        if participant["type"] == "student":
            print(f"   → Student: {participant['name']} ({participant['email']})")
        elif participant["type"] == "teacher":
            print(f"   → Teacher: {participant['name']} ({participant['email']})")
        elif participant["type"] == "section":
            print(f"   → Section: {participant['name']} ({participant['student_count']} students)")

@router.get("/tasks", response_model=List[TaskResponse])
async def get_my_tasks(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get educator's tasks/meetings with optional date filtering"""
    
    query = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.event_type == EventType.TASK
    )
    
    if start_date:
        query = query.filter(Schedule.start_datetime >= start_date)
    if end_date:
        query = query.filter(Schedule.start_datetime <= end_date)
    
    tasks = query.order_by(Schedule.start_datetime).all()
    
    response_tasks = []
    for task in tasks:
        # Extract participants from description
        participants_data = []
        if task.description and "Participants:" in task.description:
            try:
                participants_json = task.description.split("Participants:")[-1].strip()
                participants_data = json.loads(participants_json)
            except:
                participants_data = []
        
        # Extract original description (before participants)
        original_description = task.description
        if "Participants:" in task.description:
            original_description = task.description.split("\n\nParticipants:")[0]
        
        response_tasks.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=original_description,
            task_type="task",  # Default for now
            status=task.status.value,
            start=task.start_datetime.isoformat(),
            end=task.end_datetime.isoformat(),
            location=task.location or "",
            priority="medium",  # Default for now
            participants=participants_data,
            created_at=task.created_at.isoformat() if task.created_at else datetime.now().isoformat()
        ))
    
    return response_tasks

@router.post("/check-conflicts")
async def check_time_conflicts(
    conflict_data: ConflictCheckRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Check for time conflicts with existing events"""
    
    query = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.status != EventStatus.CANCELLED,
        Schedule.start_datetime < conflict_data.end_datetime,
        Schedule.end_datetime > conflict_data.start_datetime
    )
    
    if conflict_data.exclude_event_id:
        query = query.filter(Schedule.id != conflict_data.exclude_event_id)
    
    conflicts = query.all()
    
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": [
            {
                "id": conflict.id,
                "title": conflict.title,
                "start": conflict.start_datetime.isoformat(),
                "end": conflict.end_datetime.isoformat(),
                "location": conflict.location
            }
            for conflict in conflicts
        ]
    }
async def get_schedules(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_type: Optional[str] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get educator's schedule events"""
    query = db.query(Schedule).filter(Schedule.educator_id == current_educator.id)
    
    if start_date:
        query = query.filter(Schedule.start_datetime >= start_date)
    if end_date:
        query = query.filter(Schedule.end_datetime <= end_date)
    if event_type:
        query = query.filter(Schedule.event_type == event_type)
    
    schedules = query.order_by(Schedule.start_datetime).all()
    return [ScheduleResponse(**schedule.to_dict()) for schedule in schedules]

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule_event(
    schedule_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get specific schedule event"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.educator_id == current_educator.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule event not found"
        )
    
    return ScheduleResponse(**schedule.to_dict())

@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule_event(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Update schedule event"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.educator_id == current_educator.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule event not found"
        )
    
    update_data = schedule_update.dict(exclude_unset=True)
    
    # Validate status if provided
    if "status" in update_data:
        try:
            EventStatus(update_data["status"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {update_data['status']}"
            )
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    
    return ScheduleResponse(**schedule.to_dict())

@router.delete("/{schedule_id}")
async def delete_schedule_event(
    schedule_id: int,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Delete schedule event"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.educator_id == current_educator.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule event not found"
        )
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule event deleted successfully"}

@router.get("/today/events", response_model=List[ScheduleResponse])
async def get_today_events(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get today's events"""
    today = date.today()
    tomorrow = date.today().replace(day=today.day + 1)
    
    schedules = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.start_datetime >= today,
        Schedule.start_datetime < tomorrow
    ).order_by(Schedule.start_datetime).all()
    
    return [ScheduleResponse(**schedule.to_dict()) for schedule in schedules]

@router.get("/upcoming/week", response_model=List[ScheduleResponse])
async def get_week_schedule(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get upcoming week's schedule"""
    from datetime import timedelta
    
    today = date.today()
    week_end = today + timedelta(days=7)
    
    schedules = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.start_datetime >= today,
        Schedule.start_datetime <= week_end
    ).order_by(Schedule.start_datetime).all()
    
    return [ScheduleResponse(**schedule.to_dict()) for schedule in schedules]

# Task Management Models and Endpoints
class TaskType(str, enum.Enum):
    MEETING_TEACHERS = "meeting_teachers"
    PARENT_TEACHER_MEETING = "parent_teacher_meeting"
    STUDENT_REVIEW = "student_review"
    PERSONAL_REMINDER = "personal_reminder"
    EXAM_SCHEDULE = "exam_schedule"

class ParticipantType(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    SECTION = "section"

class ParticipantRequest(BaseModel):
    type: ParticipantType
    id: Optional[int] = None  # Teacher ID, Student ID, or Section ID
    email: Optional[str] = None  # For external participants
    name: Optional[str] = None  # For external participants

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 60
    location: Optional[str] = None
    participants: List[ParticipantRequest] = []
    send_notifications: bool = True
    
    @validator('scheduled_date')
    def validate_date_not_past(cls, v):
        if v < date.today():
            raise ValueError('Scheduled date cannot be in the past')
        return v

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    task_type: TaskType
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int
    location: Optional[str]
    created_by: str  # Educator name
    created_at: datetime
    updated_at: Optional[datetime]
    participants: List[Dict[str, Any]]
    is_completed: bool

class ConflictResponse(BaseModel):
    has_conflict: bool
    conflicting_tasks: List[TaskResponse]
    suggested_times: List[str]

# Simple Task model (we'll store as Schedule entries with a special type)
@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Create a new scheduled task"""
    
    # Convert participants to JSON
    participants_data = []
    for participant in task_request.participants:
        participant_info = {
            "type": participant.type.value,
            "id": participant.id,
            "email": participant.email,
            "name": participant.name
        }
        
        # Resolve names for known participants
        if participant.type == ParticipantType.TEACHER and participant.id:
            teacher = db.query(Educator).filter(Educator.id == participant.id).first()
            if teacher:
                participant_info["name"] = teacher.full_name
                participant_info["email"] = teacher.email
        elif participant.type == ParticipantType.STUDENT and participant.id:
            student = db.query(Student).filter(Student.id == participant.id).first()
            if student:
                participant_info["name"] = student.full_name
                participant_info["email"] = student.email
        elif participant.type == ParticipantType.SECTION and participant.id:
            section = db.query(Section).filter(Section.id == participant.id).first()
            if section:
                participant_info["name"] = f"Section {section.name}"
                # Get all students in section
                students = db.query(Student).filter(Student.section_id == participant.id).all()
                participant_info["student_count"] = len(students)
                participant_info["students"] = [{"id": s.id, "name": s.full_name, "email": s.email} for s in students]
        
        participants_data.append(participant_info)
    
    # Create as a Schedule entry with special handling
    start_datetime = datetime.combine(task_request.scheduled_date, task_request.scheduled_time)
    end_datetime = start_datetime + timedelta(minutes=task_request.duration_minutes)
    
    # Use custom description format to store task info
    description_data = {
        "task_type": task_request.task_type.value,
        "participants": participants_data,
        "original_description": task_request.description
    }
    
    new_schedule = Schedule(
        educator_id=current_educator.id,
        title=task_request.title,
        description=json.dumps(description_data),
        event_type=EventType.TASK,  # Assuming we add TASK to EventType enum
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        location=task_request.location,
        status=EventStatus.SCHEDULED
    )
    
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    # Send notifications in background
    if task_request.send_notifications:
        background_tasks.add_task(send_task_notifications, new_schedule.id, participants_data)
    
    return TaskResponse(
        id=new_schedule.id,
        title=new_schedule.title,
        description=task_request.description,
        task_type=task_request.task_type,
        scheduled_date=task_request.scheduled_date,
        scheduled_time=task_request.scheduled_time,
        duration_minutes=task_request.duration_minutes,
        location=new_schedule.location,
        created_by=current_educator.full_name,
        created_at=new_schedule.created_at,
        updated_at=new_schedule.updated_at,
        participants=participants_data,
        is_completed=new_schedule.status == EventStatus.COMPLETED
    )

@router.get("/tasks", response_model=List[TaskResponse])
async def get_my_tasks(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    task_type: Optional[TaskType] = None,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get all tasks for the current educator with optional filtering"""
    
    query = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.event_type == EventType.TASK
    )
    
    if start_date:
        query = query.filter(Schedule.start_datetime >= start_date)
    if end_date:
        end_datetime = datetime.combine(end_date, time.max)
        query = query.filter(Schedule.start_datetime <= end_datetime)
    
    schedules = query.order_by(Schedule.start_datetime).all()
    
    result = []
    for schedule in schedules:
        try:
            description_data = json.loads(schedule.description) if schedule.description else {}
            stored_task_type = description_data.get("task_type", "personal_reminder")
            
            # Filter by task type if specified
            if task_type and stored_task_type != task_type.value:
                continue
                
            participants = description_data.get("participants", [])
            original_description = description_data.get("original_description")
            
            result.append(TaskResponse(
                id=schedule.id,
                title=schedule.title,
                description=original_description,
                task_type=TaskType(stored_task_type),
                scheduled_date=schedule.start_datetime.date(),
                scheduled_time=schedule.start_datetime.time(),
                duration_minutes=int((schedule.end_datetime - schedule.start_datetime).total_seconds() / 60),
                location=schedule.location,
                created_by=current_educator.full_name,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
                participants=participants,
                is_completed=schedule.status == EventStatus.COMPLETED
            ))
        except (json.JSONDecodeError, ValueError):
            # Skip malformed task data
            continue
    
    return result

@router.get("/tasks/conflicts")
async def check_time_conflicts(
    scheduled_date: date,
    scheduled_time: time,
    duration_minutes: int = 60,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Check for scheduling conflicts on a given date and time"""
    
    # Convert to datetime for easier comparison
    requested_datetime = datetime.combine(scheduled_date, scheduled_time)
    end_datetime = requested_datetime + timedelta(minutes=duration_minutes)
    
    # Get all schedule events on the same date
    day_start = datetime.combine(scheduled_date, time.min)
    day_end = datetime.combine(scheduled_date, time.max)
    
    existing_schedules = db.query(Schedule).filter(
        Schedule.educator_id == current_educator.id,
        Schedule.start_datetime >= day_start,
        Schedule.start_datetime <= day_end
    ).all()
    
    conflicting_tasks = []
    for schedule in existing_schedules:
        # Check for overlap
        if (requested_datetime < schedule.end_datetime and end_datetime > schedule.start_datetime):
            try:
                description_data = json.loads(schedule.description) if schedule.description else {}
                participants = description_data.get("participants", [])
                task_type_str = description_data.get("task_type", "personal_reminder")
                original_description = description_data.get("original_description")
                
                conflicting_tasks.append(TaskResponse(
                    id=schedule.id,
                    title=schedule.title,
                    description=original_description,
                    task_type=TaskType(task_type_str),
                    scheduled_date=schedule.start_datetime.date(),
                    scheduled_time=schedule.start_datetime.time(),
                    duration_minutes=int((schedule.end_datetime - schedule.start_datetime).total_seconds() / 60),
                    location=schedule.location,
                    created_by=current_educator.full_name,
                    created_at=schedule.created_at,
                    updated_at=schedule.updated_at,
                    participants=participants,
                    is_completed=schedule.status == EventStatus.COMPLETED
                ))
            except (json.JSONDecodeError, ValueError):
                # Handle regular schedule events
                conflicting_tasks.append(TaskResponse(
                    id=schedule.id,
                    title=schedule.title,
                    description=schedule.description,
                    task_type=TaskType.PERSONAL_REMINDER,
                    scheduled_date=schedule.start_datetime.date(),
                    scheduled_time=schedule.start_datetime.time(),
                    duration_minutes=int((schedule.end_datetime - schedule.start_datetime).total_seconds() / 60),
                    location=schedule.location,
                    created_by=current_educator.full_name,
                    created_at=schedule.created_at,
                    updated_at=schedule.updated_at,
                    participants=[],
                    is_completed=schedule.status == EventStatus.COMPLETED
                ))
    
    # Generate suggested alternative times
    suggested_times = []
    if conflicting_tasks:
        # Simple suggestion: try 1 hour before and after
        suggestion_before = (requested_datetime - timedelta(hours=1)).time().strftime("%H:%M")
        suggestion_after = (requested_datetime + timedelta(hours=1)).time().strftime("%H:%M")
        suggested_times = [suggestion_before, suggestion_after]
    
    return ConflictResponse(
        has_conflict=len(conflicting_tasks) > 0,
        conflicting_tasks=conflicting_tasks,
        suggested_times=suggested_times
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
        event_data = {
            "id": schedule.id,
            "title": schedule.title,
            "start": schedule.start_datetime.isoformat(),
            "end": schedule.end_datetime.isoformat(),
            "location": schedule.location,
            "type": schedule.event_type.value,
            "status": schedule.status.value
        }
        
        # If it's a task, extract additional info
        if schedule.event_type == EventType.TASK:
            try:
                description_data = json.loads(schedule.description) if schedule.description else {}
                event_data["task_type"] = description_data.get("task_type")
                event_data["participants"] = description_data.get("participants", [])
                event_data["description"] = description_data.get("original_description")
            except json.JSONDecodeError:
                event_data["description"] = schedule.description
        else:
            event_data["description"] = schedule.description
        
        calendar_events.append(event_data)
    
    return {"events": calendar_events, "total": len(calendar_events)}

@router.get("/sections/{section_id}/students")
async def get_section_students_for_scheduling(
    section_id: int,
    criteria: Optional[str] = "all",  # all, top_performers, low_performers, range
    count: Optional[int] = None,
    range_start: Optional[int] = None,  # For range selection (roll number start)
    range_end: Optional[int] = None,    # For range selection (roll number end)
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """Get students from a section for scheduling purposes with range selection support"""
    
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
    
    # Create criteria object for selection
    selection_criteria = StudentSelectionCriteria(
        section_id=section_id,
        criteria=criteria,
        count=count,
        range_start=range_start,
        range_end=range_end
    )
    
    # Get students using the enhanced selection function
    selected_students = select_students_by_criteria(
        db, section_id, selection_criteria, current_educator
    )
    
    students_data = []
    for student in selected_students:
        # Calculate average grade for display
        grades = [grade.grade_value for grade in student.grades if grade.grade_value]
        avg_grade = sum(grades) / len(grades) if grades else 0
        
        # Extract roll number from student_id
        try:
            roll_number = int(student.student_id.lstrip('0')) if student.student_id else 0
        except (ValueError, AttributeError):
            roll_number = 0
        
        students_data.append({
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "email": student.email,
            "student_id": student.student_id,
            "roll_number": roll_number,
            "average_grade": round(avg_grade, 2)
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

async def send_task_notifications(task_id: int, participants: List[Dict]):
    """Background task to send notifications to participants"""
    # This would integrate with the notification system
    # For now, just log the notification
    print(f"Sending notifications for task {task_id} to {len(participants)} participants")
    # TODO: Implement actual notification sending using the communication system