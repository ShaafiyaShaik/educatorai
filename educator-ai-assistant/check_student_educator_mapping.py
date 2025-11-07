#!/usr/bin/env python3
"""
Check student-educator mapping and task visibility
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.student import Student
from app.models.educator import Educator
from app.models.section import Section
from app.models.task_schedule import TaskSchedule
from sqlalchemy.orm import sessionmaker

def check_student_educator_mapping():
    """Check how students are mapped to educators"""
    print("🔍 Checking Student-Educator Mapping")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get Ananya
        ananya = session.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        print(f"👩‍🏫 Ananya's ID: {ananya.id}")
        
        # Get all students
        students = session.query(Student).all()
        print(f"\n📚 Total Students: {len(students)}")
        
        print("\n🎓 STUDENT DETAILS:")
        print("-" * 60)
        
        for student in students:
            # Get student's section
            section = session.query(Section).filter(Section.id == student.section_id).first() if hasattr(student, 'section_id') and student.section_id else None
            
            print(f"ID: {student.id} | {student.first_name} {student.last_name}")
            print(f"   Email: {student.email}")
            if hasattr(student, 'section_id'):
                print(f"   Section ID: {student.section_id}")
            else:
                print("   Section ID: NOT FOUND")
                
            if section:
                print(f"   Section: {section.name}")
                print(f"   Educator ID: {section.educator_id}")
                if section.educator_id == ananya.id:
                    print("   ✅ ANANYA'S STUDENT")
                else:
                    other_educator = session.query(Educator).filter(Educator.id == section.educator_id).first()
                    print(f"   ❌ NOT Ananya's (belongs to {other_educator.first_name if other_educator else 'Unknown'})")
            else:
                print("   ❌ NO SECTION ASSIGNED")
            print()
        
        # Check tasks
        tasks = session.query(TaskSchedule).all()
        print(f"📋 SCHEDULED TASKS: {len(tasks)}")
        print("-" * 60)
        
        for task in tasks:
            educator = session.query(Educator).filter(Educator.id == task.educator_id).first()
            print(f"Task: {task.title}")
            print(f"   Created by: {educator.first_name if educator else 'Unknown'} (ID: {task.educator_id})")
            print(f"   Recipients: {task.recipients}")
            print(f"   Recipient Type: {task.recipient_type}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_student_educator_mapping()