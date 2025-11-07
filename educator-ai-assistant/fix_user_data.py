"""
Check existing educators and update data for the correct user
"""

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.models.student import Section, Student

def check_and_fix_user_data():
    db = SessionLocal()
    try:
        # Check all educators
        all_educators = db.query(Educator).all()
        print("All educators in database:")
        for educator in all_educators:
            print(f"  ID: {educator.id}, Email: {educator.email}, Name: {educator.first_name} {educator.last_name}")
            
        # Check which educator has the sections with students
        sections_with_students = db.query(Section).all()
        print(f"\nSections and their educators:")
        for section in sections_with_students:
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            educator = db.query(Educator).filter(Educator.id == section.educator_id).first()
            educator_email = educator.email if educator else "Unknown"
            print(f"  Section {section.id} ({section.name}): {student_count} students, educator: {educator_email}")
            
        # Check if shaaf123@gmail.com exists
        target_educator = db.query(Educator).filter(Educator.email == "shaaf123@gmail.com").first()
        if target_educator:
            print(f"\nFound target educator: {target_educator.email} (ID: {target_educator.id})")
            
            # Move sections to this educator
            educator_with_data = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
            if educator_with_data:
                print(f"Moving sections from {educator_with_data.email} to {target_educator.email}")
                
                # Update all sections to belong to the correct educator
                sections_to_move = db.query(Section).filter(Section.educator_id == educator_with_data.id).all()
                for section in sections_to_move:
                    section.educator_id = target_educator.id
                    print(f"  Moved section {section.name} to {target_educator.email}")
                
                db.commit()
                print("✅ Sections moved successfully!")
            else:
                print("⚠️ No educator with data found to move from")
        else:
            print(f"\n❌ Target educator shaaf123@gmail.com not found!")
            print("Available educators:")
            for educator in all_educators:
                print(f"  - {educator.email}")
                
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_user_data()