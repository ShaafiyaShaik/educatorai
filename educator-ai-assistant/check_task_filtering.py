#!/usr/bin/env python3
"""
Direct database check for task filtering issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.schedule import Schedule
from app.models.student import Student, Section  
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker
import json

def check_task_filtering():
    """Check why tasks are showing to all students"""
    print("🔍 Direct Database Check - Task Filtering Issue")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 1. Get all tasks
        tasks = session.query(Schedule).filter(Schedule.event_type == "task").all()
        print(f"📋 Total Tasks: {len(tasks)}")
        
        for task in tasks:
            print(f"\n📝 Task ID {task.id}: {task.title}")
            print(f"   Created by Educator ID: {task.educator_id}")
            print(f"   Participants JSON: {task.participants}")
            
            # Get the educator who created it
            educator = session.query(Educator).filter(Educator.id == task.educator_id).first()
            print(f"   Educator: {educator.first_name if educator else 'Unknown'}")
            
        # 2. Get Ananya's details
        print(f"\n👩‍🏫 ANANYA'S DATA:")
        print("-" * 40)
        ananya = session.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        if ananya:
            print(f"   ID: {ananya.id}")
            
            # Get her sections
            sections = session.query(Section).filter(Section.educator_id == ananya.id).all()
            print(f"   Sections: {[s.id for s in sections]}")
            
            for section in sections:
                students = session.query(Student).filter(Student.section_id == section.id).all()
                print(f"   Section {section.id} ({section.name}):")
                for student in students:
                    print(f"      - {student.student_id}: {student.first_name} {student.last_name} (section_id: {student.section_id})")
                    
        # 3. Get Aditya's details  
        print(f"\n🎓 ADITYA'S DATA:")
        print("-" * 40)
        aditya = session.query(Student).filter(Student.email == "aditya.s301@school.com").first()
        if aditya:
            print(f"   ID: {aditya.id}")
            print(f"   Student ID: {aditya.student_id}")
            print(f"   Section ID: {aditya.section_id}")
            
            if aditya.section_id:
                section = session.query(Section).filter(Section.id == aditya.section_id).first()
                if section:
                    print(f"   Section: {section.name}")
                    print(f"   Section's Educator ID: {section.educator_id}")
                    educator = session.query(Educator).filter(Educator.id == section.educator_id).first()
                    print(f"   Educator: {educator.first_name if educator else 'Unknown'}")
                    
        # 4. Get Rahul's details
        print(f"\n🎓 RAHUL'S DATA:")
        print("-" * 40)
        rahul = session.query(Student).filter(Student.email == "rahul.s101@school.com").first()
        if rahul:
            print(f"   ID: {rahul.id}")
            print(f"   Student ID: {rahul.student_id}")
            print(f"   Section ID: {rahul.section_id}")
            
            if rahul.section_id:
                section = session.query(Section).filter(Section.id == rahul.section_id).first()
                if section:
                    print(f"   Section: {section.name}")
                    print(f"   Section's Educator ID: {section.educator_id}")
                    educator = session.query(Educator).filter(Educator.id == section.educator_id).first()
                    print(f"   Educator: {educator.first_name if educator else 'Unknown'}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_task_filtering()