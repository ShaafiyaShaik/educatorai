#!/usr/bin/env python3
"""
Debug the scheduled task data to see what's stored
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.models.schedule import Schedule, EventType
import json

def debug_scheduled_tasks():
    db = next(get_db())
    
    print("🔍 DEBUGGING SCHEDULED TASKS")
    print("=" * 50)
    
    # Get Shaaf
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    print(f"Educator: {shaaf.first_name} {shaaf.last_name} (ID: {shaaf.id})")
    
    # Get all scheduled tasks
    tasks = db.query(Schedule).filter(
        Schedule.educator_id == shaaf.id,
        Schedule.event_type == EventType.TASK
    ).order_by(Schedule.start_datetime).all()
    
    print(f"\n📋 Found {len(tasks)} scheduled tasks:")
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{i}. Task ID: {task.id}")
        print(f"   Title: {task.title}")
        print(f"   Description: {task.description}")
        print(f"   Start: {task.start_datetime}")
        print(f"   End: {task.end_datetime}")
        print(f"   Location: {task.location}")
        
        # Check what date this represents
        if task.start_datetime:
            local_date = task.start_datetime.date()
            print(f"   Local Date: {local_date}")
            print(f"   Time: {task.start_datetime.time()}")
            print(f"   ISO String: {task.start_datetime.isoformat()}")
        
        # Calculate duration
        if task.end_datetime and task.start_datetime:
            duration = task.end_datetime - task.start_datetime
            duration_minutes = int(duration.total_seconds() / 60)
            print(f"   Duration: {duration_minutes} minutes")
    
    db.close()

if __name__ == "__main__":
    debug_scheduled_tasks()