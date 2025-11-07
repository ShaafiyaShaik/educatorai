"""
Check which educator owns the sections with students and grades
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.educator import Educator
from app.models.student import Student, Section, Grade

def check_educator_sections():
    """Check which educator has sections with students and grades"""
    db = next(get_db())
    
    try:
        print("🔍 CHECKING EDUCATOR-SECTION MAPPING")
        print("=" * 50)
        
        # Get all educators
        educators = db.query(Educator).all()
        
        for educator in educators:
            print(f"\n👩‍🏫 {educator.first_name} {educator.last_name} (ID: {educator.id})")
            print(f"   Email: {educator.email}")
            
            # Get sections for this educator
            sections = db.query(Section).filter(Section.educator_id == educator.id).all()
            print(f"   Sections: {len(sections)}")
            
            total_students = 0
            total_grades = 0
            
            for section in sections:
                students = db.query(Student).filter(Student.section_id == section.id).all()
                grades_count = db.query(Grade).join(Student).filter(
                    Student.section_id == section.id
                ).count()
                
                print(f"     - {section.name} (ID: {section.id}): {len(students)} students, {grades_count} grades")
                total_students += len(students)
                total_grades += grades_count
            
            print(f"   Total: {total_students} students, {total_grades} grades")
            
            if total_grades > 0:
                print(f"   ✅ This educator has performance data!")
        
        # Also check which sections have grades but no educator assignment
        print(f"\n🔍 CHECKING UNASSIGNED SECTIONS")
        print("=" * 30)
        
        sections_with_grades = db.query(Section).join(Student).join(Grade).distinct().all()
        
        for section in sections_with_grades:
            students = db.query(Student).filter(Student.section_id == section.id).all()
            grades_count = db.query(Grade).join(Student).filter(
                Student.section_id == section.id
            ).count()
            
            educator = db.query(Educator).filter(Educator.id == section.educator_id).first()
            educator_name = f"{educator.first_name} {educator.last_name}" if educator else "UNASSIGNED"
            
            print(f"Section: {section.name} -> Educator: {educator_name}")
            print(f"  Students: {len(students)}, Grades: {grades_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_educator_sections()