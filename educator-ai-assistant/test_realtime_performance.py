"""
Test Real-time Performance Updates
This script simulates data changes to test WebSocket real-time updates
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.student import Student, Grade, Subject
from app.models.performance import Attendance, Exam
from app.api.performance_views import notify_grade_update, notify_attendance_update, notify_exam_created
from datetime import datetime, date
import random

def test_realtime_updates():
    """Test real-time performance updates by making data changes"""
    db = next(get_db())
    
    try:
        print("🚀 Testing Real-time Performance Updates...")
        
        # Test 1: Add a new grade
        print("\n1. Adding a new grade...")
        students = db.query(Student).limit(3).all()
        subjects = db.query(Subject).limit(3).all()
        
        if students and subjects:
            student = students[0]
            subject = subjects[0]
            
            # Create new grade
            new_grade = Grade(
                student_id=student.id,
                subject_id=subject.id,
                score=random.randint(70, 95),
                total_marks=100,
                grade_date=datetime.now().date(),
                remarks=f"Test grade - {datetime.now().strftime('%H:%M:%S')}"
            )
            
            db.add(new_grade)
            db.commit()
            print(f"✅ Added grade for {student.name} in {subject.name}: {new_grade.score}/100")
            
            # Trigger real-time notification
            asyncio.create_task(notify_grade_update(new_grade, db))
            
        # Test 2: Update attendance
        print("\n2. Adding attendance record...")
        if students:
            student = students[1] if len(students) > 1 else students[0]
            
            # Create attendance record
            new_attendance = Attendance(
                student_id=student.id,
                date=date.today(),
                status=random.choice(['present', 'absent']),
                remarks=f"Test attendance - {datetime.now().strftime('%H:%M:%S')}"
            )
            
            db.add(new_attendance)
            db.commit()
            print(f"✅ Added attendance for {student.name}: {new_attendance.status}")
            
            # Trigger real-time notification
            asyncio.create_task(notify_attendance_update(new_attendance, db))
            
        # Test 3: Create a new exam
        print("\n3. Creating a new exam...")
        if subjects:
            subject = subjects[1] if len(subjects) > 1 else subjects[0]
            
            # Get a section
            sections = db.query(Student.section_id).distinct().limit(1).all()
            if sections:
                section_id = sections[0][0]
                
                new_exam = Exam(
                    name=f"Test Exam {datetime.now().strftime('%H:%M:%S')}",
                    subject_id=subject.id,
                    section_id=section_id,
                    exam_date=date.today(),
                    total_marks=100,
                    duration_minutes=120,
                    exam_type="Quiz"
                )
                
                db.add(new_exam)
                db.commit()
                print(f"✅ Created exam: {new_exam.name} for {subject.name}")
                
                # Trigger real-time notification
                asyncio.create_task(notify_exam_created(new_exam, db))
        
        print("\n🎉 Real-time update tests completed!")
        print("📊 Check the Performance Dashboard to see live updates")
        print("🔗 WebSocket should show real-time notifications")
        
    except Exception as e:
        print(f"❌ Error in real-time testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

async def run_continuous_updates():
    """Run continuous updates for testing real-time functionality"""
    print("🔄 Starting continuous updates (Press Ctrl+C to stop)...")
    
    try:
        while True:
            print(f"\n⏱️  {datetime.now().strftime('%H:%M:%S')} - Triggering update...")
            test_realtime_updates()
            
            # Wait 15 seconds before next update
            await asyncio.sleep(15)
            
    except KeyboardInterrupt:
        print("\n🛑 Continuous updates stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test real-time performance updates')
    parser.add_argument('--continuous', action='store_true', help='Run continuous updates')
    
    args = parser.parse_args()
    
    if args.continuous:
        asyncio.run(run_continuous_updates())
    else:
        test_realtime_updates()