"""
Test performance calculation directly
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Grade
from app.models.educator import Educator
from app.api.performance_views import calculate_student_performance_detailed, get_section_performance
from sqlalchemy.orm import joinedload

def test_performance():
    """Test performance calculations step by step"""
    db = next(get_db())
    
    # Get educator with ID 1
    educator = db.query(Educator).filter(Educator.id == 1).first()
    print(f"Testing with educator: {educator.full_name} ({educator.email})")
    
    # Get their sections
    sections = db.query(Section).filter(Section.educator_id == 1).all()
    print(f"Sections: {len(sections)}")
    
    for section in sections:
        print(f"\n=== Section: {section.name} ===")
        students = db.query(Student).filter(Student.section_id == section.id).all()
        print(f"Students in section: {len(students)}")
        
        for student in students[:2]:  # Test first 2 students
            print(f"\nTesting student: {student.full_name}")
            
            # Check grades
            grades = db.query(Grade).filter(Grade.student_id == student.id).all()
            print(f"Grades for student: {len(grades)}")
            
            if grades:
                for grade in grades[:3]:  # Show first 3 grades
                    print(f"  - {grade.subject.name if grade.subject else 'Unknown'}: {grade.marks_obtained}/{grade.total_marks}")
                
                # Test performance calculation
                try:
                    perf = calculate_student_performance_detailed(student, db)
                    print(f"Performance: {perf.average_score}% ({perf.status})")
                except Exception as e:
                    print(f"ERROR calculating performance: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("  No grades found for student")
        
        # Test section performance
        print(f"\n--- Section Performance for {section.name} ---")
        try:
            section_perf = get_section_performance(section.id, db, educator.id)
            print(f"Section average: {section_perf.average_score}%")
            print(f"Pass rate: {section_perf.pass_rate}%")
            print(f"Total students: {section_perf.total_students}")
        except Exception as e:
            print(f"ERROR calculating section performance: {e}")
            import traceback
            traceback.print_exc()
            
        break  # Only test first section for now
    
    db.close()

if __name__ == "__main__":
    test_performance()