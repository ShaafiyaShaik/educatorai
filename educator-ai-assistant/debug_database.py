"""
Debug database relationships
"""

from app.core.database import SessionLocal
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator

def debug_database():
    db = SessionLocal()
    try:
        # Get the test educator
        educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        print(f"Educator: {educator.email} (ID: {educator.id})")
        
        # Get all sections
        all_sections = db.query(Section).all()
        print(f"\nAll sections in database: {len(all_sections)}")
        for section in all_sections:
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            print(f"  Section {section.id}: {section.name} (educator_id: {section.educator_id}) - {student_count} students")
        
        # Get educator's sections
        educator_sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"\nEducator's sections: {len(educator_sections)}")
        for section in educator_sections:
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            print(f"  Section {section.id}: {section.name} - {student_count} students")
        
        # Get all students
        all_students = db.query(Student).all()
        print(f"\nAll students in database: {len(all_students)}")
        
        # Show section distribution of students
        section_distribution = {}
        for student in all_students:
            if student.section_id not in section_distribution:
                section_distribution[student.section_id] = 0
            section_distribution[student.section_id] += 1
        
        print(f"\nStudent distribution by section_id:")
        for section_id, count in section_distribution.items():
            section = db.query(Section).filter(Section.id == section_id).first()
            section_name = section.name if section else "Unknown"
            educator_id = section.educator_id if section else "Unknown"
            print(f"  Section {section_id} ({section_name}, educator_id: {educator_id}): {count} students")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_database()