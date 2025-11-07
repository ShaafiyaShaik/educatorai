"""
Direct test of students endpoint with manual section check
"""

from app.core.database import SessionLocal
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator

def test_section_lookup():
    db = SessionLocal()
    try:
        # Get the test educator
        educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        print(f"Educator: {educator.email} (ID: {educator.id})")
        
        # Test the exact query from the API
        section_id = 10  # This is what we're testing
        section = db.query(Section).filter(
            Section.id == section_id,
            Section.educator_id == educator.id
        ).first()
        
        print(f"Section lookup for ID {section_id}:")
        if section:
            print(f"  Found: {section.name} (ID: {section.id}, educator_id: {section.educator_id})")
            
            # Get students in this section
            students = db.query(Student).filter(Student.section_id == section_id).all()
            print(f"  Students: {len(students)}")
            
            if students:
                print(f"  First student: {students[0].first_name} {students[0].last_name}")
        else:
            print(f"  Section not found!")
            
            # Check what section 10 actually looks like
            actual_section = db.query(Section).filter(Section.id == section_id).first()
            if actual_section:
                print(f"  But section {section_id} exists with educator_id: {actual_section.educator_id}")
            else:
                print(f"  Section {section_id} doesn't exist at all!")
                
    finally:
        db.close()

if __name__ == "__main__":
    test_section_lookup()