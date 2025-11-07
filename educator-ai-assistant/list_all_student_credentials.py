#!/usr/bin/env python3
"""
List all student credentials organized by section
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from app.models.student import Section, Student
from sqlalchemy.orm import sessionmaker

def list_all_student_credentials():
    """List all student credentials organized by section and educator"""
    print("🎓 ALL STUDENT CREDENTIALS")
    print("=" * 80)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get all educators
        educators = session.query(Educator).all()
        
        for educator in educators:
            print(f"\n👨‍🏫 EDUCATOR: {educator.first_name} {educator.last_name}")
            print(f"📧 Email: {educator.email}")
            print("─" * 60)
            
            # Get sections for this educator
            sections = session.query(Section).filter(Section.educator_id == educator.id).all()
            
            if not sections:
                print("   📝 No sections assigned to this educator")
                continue
                
            for section in sections:
                print(f"\n📚 SECTION: {section.name}")
                print("─" * 40)
                
                # Get students in this section
                students = session.query(Student).filter(Student.section_id == section.id).all()
                
                if not students:
                    print("   📝 No students in this section")
                else:
                    for i, student in enumerate(students, 1):
                        print(f"   {i:2d}. 🎓 {student.first_name} {student.last_name}")
                        print(f"       📧 Email: {student.email}")
                        print(f"       🔑 Password: student123")
                        print(f"       🆔 Student ID: {student.student_id}")
                        print(f"       📋 Roll Number: {student.roll_number}")
                        print()
        
        # Summary of all credentials
        print("\n" + "=" * 80)
        print("📋 QUICK REFERENCE - ALL STUDENT LOGIN CREDENTIALS")
        print("=" * 80)
        
        all_students = session.query(Student).all()
        
        # Group by section for better organization
        sections_dict = {}
        for student in all_students:
            section = session.query(Section).filter(Section.id == student.section_id).first()
            educator = session.query(Educator).filter(Educator.id == section.educator_id).first() if section else None
            
            section_name = section.name if section else "Unknown Section"
            educator_name = f"{educator.first_name} {educator.last_name}" if educator else "Unknown Educator"
            
            if section_name not in sections_dict:
                sections_dict[section_name] = {
                    'educator': educator_name,
                    'students': []
                }
            
            sections_dict[section_name]['students'].append({
                'name': f"{student.first_name} {student.last_name}",
                'email': student.email,
                'student_id': student.student_id
            })
        
        for section_name, section_info in sections_dict.items():
            print(f"\n📚 {section_name} ({section_info['educator']})")
            print("─" * 50)
            for student in section_info['students']:
                print(f"   📧 {student['email']} | 🔑 student123")
                print(f"   👤 {student['name']} (ID: {student['student_id']})")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    list_all_student_credentials()