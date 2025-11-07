#!/usr/bin/env python3
"""
List student credentials for Ananya's sections
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from app.models.student import Section, Student
from sqlalchemy.orm import sessionmaker

def list_student_credentials():
    """List all student accounts and their credentials"""
    print("🎓 Student Account Credentials")
    print("=" * 50)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Find Ananya's educator record
        ananya = session.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        
        if not ananya:
            print("❌ Ananya not found in database")
            return
            
        print(f"👨‍🏫 Educator: {ananya.first_name} {ananya.last_name}")
        print(f"📧 Email: {ananya.email}")
        print()
        
        # Find Ananya's sections
        sections = session.query(Section).filter(Section.educator_id == ananya.id).all()
        
        print(f"🏫 Ananya's Sections ({len(sections)} total):")
        for section in sections:
            print(f"\n📚 Section: {section.name} (ID: {section.id})")
            
            # Find students in this section
            students = session.query(Student).filter(Student.section_id == section.id).all()
            
            if students:
                print(f"   👥 Students ({len(students)} total):")
                for student in students:
                    print(f"      🎓 {student.first_name} {student.last_name}")
                    print(f"         📧 Email: {student.email}")
                    print(f"         🔑 Password: student123")
                    print(f"         🆔 Student ID: {student.student_id}")
                    print(f"         📋 Roll Number: {student.roll_number}")
                    print(f"         ✅ Active: {student.is_active}")
                    print()
            else:
                print("   📝 No students in this section")
        
        # Also list all students for reference
        print("\n" + "=" * 50)
        print("📋 All Student Accounts Summary:")
        print("=" * 50)
        
        all_students = session.query(Student).all()
        for student in all_students:
            section = session.query(Section).filter(Section.id == student.section_id).first()
            educator = session.query(Educator).filter(Educator.id == section.educator_id).first() if section else None
            
            print(f"🎓 {student.first_name} {student.last_name}")
            print(f"   📧 {student.email} | 🔑 student123")
            print(f"   📚 Section: {section.name if section else 'Unknown'}")
            print(f"   👨‍🏫 Educator: {educator.first_name + ' ' + educator.last_name if educator else 'Unknown'}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    list_student_credentials()