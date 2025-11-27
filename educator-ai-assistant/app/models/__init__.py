# Import all models to ensure they're registered with SQLAlchemy
from .educator import Educator
from .student import Student, Section, Subject, Grade
from .schedule import Schedule
from .record import Record
from .compliance import ComplianceReport
from .meeting_request import MeetingRequest
from .meeting_schedule import Meeting, MeetingRecipient
from .communication import Communication
from .notification import Notification
from .report import SentReport
from .performance import Exam, Attendance, PerformanceCache, StudentPerformanceSummary
from .action_log import ActionLog

__all__ = [
    "Educator",
    "Student", 
    "Section",
    "Subject",
    "Grade",
    "Schedule",
    "Record", 
    "ComplianceReport",
    "MeetingRequest",
    "Meeting",
    "MeetingRecipient", 
    "Communication",
    "Notification",
    "SentReport",
    "Exam",
    "Attendance",
    "PerformanceCache",
    "StudentPerformanceSummary"
    ,
    "ActionLog"
]