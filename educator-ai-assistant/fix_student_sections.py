"""
Fix student-section relationships for our test educator
"""

from app.core.database import SessionLocal
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator

def fix_student_sections():
    db = SessionLocal()
    try:
        # Get the test educator
        educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        print(f"Educator: {educator.email} (ID: {educator.id})")
        
        # Get educator's sections
        educator_sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"Educator's sections: {[s.id for s in educator_sections]}")
        
        if len(educator_sections) < 3:
            print("Not enough sections for educator!")
            return
            
        # Get students from sections 1, 2, 3 (which have students) and move them to our sections
        old_sections = [1, 2, 3]  # These have students but belong to educator_id 2
        
        for i, old_section_id in enumerate(old_sections):
            new_section = educator_sections[i]
            
            # Move students from old section to new section
            students_to_move = db.query(Student).filter(Student.section_id == old_section_id).all()
            print(f"Moving {len(students_to_move)} students from section {old_section_id} to section {new_section.id}")
            
            for student in students_to_move:
                student.section_id = new_section.id
            
            db.commit()
            
        # Verify the move
        print("\nAfter moving:")
        for section in educator_sections:
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            print(f"  Section {section.id}: {section.name} - {student_count} students")
            
    finally:
        db.close()

if __name__ == "__main__":
    fix_student_sections()