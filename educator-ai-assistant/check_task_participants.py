#!/usr/bin/env python3
"""
Check what's in the participants field for the scheduled task
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.task_schedule import TaskSchedule
from app.models.student import Student  
from app.models.section import Section
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker
import json

def check_task_participants():
    """Check the participants data structure"""
    print("🔍 Checking Task Participants Data")
    print("=" * 50)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get the task
        tasks = session.query(TaskSchedule).all()
        if not tasks:
            print("❌ No tasks found!")
            return
            
        for task in tasks:
            print(f"📋 Task: {task.title}")
            print(f"   Recipients: {task.recipients}")
            print(f"   Recipient Type: {task.recipient_type}")
            
            # Parse recipients
            try:
                recipients_data = json.loads(task.recipients) if task.recipients else {}
                print(f"   Parsed Recipients: {recipients_data}")
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON in recipients!")
                
        # Check Ananya's students
        ananya = session.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        if ananya:
            print(f"\n👩‍🏫 Ananya's ID: {ananya.id}")
            
            # Get Ananya's sections
            ananya_sections = session.query(Section).filter(Section.educator_id == ananya.id).all()
            print(f"📚 Ananya's Sections: {[s.id for s in ananya_sections]}")
            
            for section in ananya_sections:
                students = session.query(Student).filter(Student.section_id == section.id).all()
                print(f"   Section {section.id} ({section.name}): {len(students)} students")
                for student in students:
                    print(f"      - {student.student_id}: {student.first_name} {student.last_name}")
                    
        # Check Aditya's details
        print(f"\n🎓 Checking Aditya:")
        aditya = session.query(Student).filter(Student.email == "aditya.s301@school.com").first()
        if aditya:
            print(f"   ID: {aditya.id}, Student ID: {aditya.student_id}")
            print(f"   Section ID: {getattr(aditya, 'section_id', 'NOT FOUND')}")
            
            if hasattr(aditya, 'section_id') and aditya.section_id:
                section = session.query(Section).filter(Section.id == aditya.section_id).first()
                if section:
                    print(f"   Section: {section.name} (Educator ID: {section.educator_id})")
                    educator = session.query(Educator).filter(Educator.id == section.educator_id).first()
                    print(f"   Educator: {educator.first_name if educator else 'Unknown'}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_task_participants()