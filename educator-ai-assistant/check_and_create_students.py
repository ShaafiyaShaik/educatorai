"""
Check and create student data for testing
"""

from app.core.database import SessionLocal, engine
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Base, Educator
import random

def create_sample_data():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Get the test educator
        educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        if not educator:
            print("Test educator not found! Creating...")
            from app.core.auth import get_password_hash
            educator = Educator(
                email="shaaf@gmail.com",
                password_hash=get_password_hash("password123"),
                first_name="Shaaf",
                last_name="Test",
                title="Teacher",
                department="Computer Science",
                office_location="Room 101",
                phone="555-0123"
            )
            db.add(educator)
            db.commit()
            
        print(f"Using educator: {educator.email} (ID: {educator.id})")
        
        # Check if we have sections
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        if not sections:
            print("Creating sections...")
            for section_name in ['A', 'B', 'C']:
                section = Section(
                    name=f"Section {section_name}",
                    educator_id=educator.id,
                    description=f"Class Section {section_name}",
                    grade_level=10,
                    academic_year="2024-2025"
                )
                db.add(section)
            db.commit()
            
        # Refresh sections
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"Found {len(sections)} sections for educator")
        
        # Check if we have subjects
        subjects = db.query(Subject).all()
        if not subjects:
            print("Creating subjects...")
            for subject_name in ['Math', 'Science', 'English']:
                subject = Subject(
                    name=subject_name,
                    code=subject_name.upper()[:3]
                )
                db.add(subject)
            db.commit()
            
        # Refresh subjects
        subjects = db.query(Subject).all()
        print(f"Found {len(subjects)} subjects")
        
        # Check if we have students
        students = db.query(Student).all()
        if len(students) < 150:  # We want 50 per section
            print("Creating students...")
            
            # Clear existing students and grades
            db.query(Grade).delete()
            db.query(Student).delete()
            db.commit()
            
            first_names = [
                "Emma", "Liam", "Olivia", "Noah", "Ava", "Elijah", "Charlotte", "Oliver", "Amelia", "James",
                "Sophia", "Benjamin", "Isabella", "Lucas", "Mia", "Henry", "Evelyn", "Alexander", "Harper", "Mason",
                "Camila", "Michael", "Gianna", "Ethan", "Abigail", "Daniel", "Luna", "Matthew", "Ella", "Anthony",
                "Elizabeth", "Jackson", "Sofia", "David", "Emily", "Samuel", "Avery", "Joseph", "Mila", "Owen",
                "Scarlett", "Sebastian", "Eleanor", "John", "Madison", "Andrew", "Layla", "Elias", "Penelope", "Joshua"
            ]
            
            last_names = [
                "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
                "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
                "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
            ]
            
            for section in sections:
                for i in range(50):  # 50 students per section
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    student_id = f"{section.name.split()[-1]}{i+1:03d}"  # A001, A002, etc.
                    
                    student = Student(
                        student_id=student_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=f"{first_name.lower()}.{last_name.lower()}@student.school.edu",
                        section_id=section.id,
                        grade_level=10,
                        date_of_birth="2008-01-01",  # Simplified
                        enrollment_date="2024-08-01"
                    )
                    db.add(student)
                    db.commit()  # Commit to get student ID
                    
                    # Create grades for each subject
                    for subject in subjects:
                        # Generate realistic grades
                        grade_value = random.randint(30, 100)
                        grade = Grade(
                            student_id=student.id,
                            subject_id=subject.id,
                            grade_value=grade_value,
                            max_grade=100,
                            assessment_type="Test",
                            date_recorded="2024-09-01"
                        )
                        db.add(grade)
                    
                db.commit()
                print(f"Created 50 students for {section.name}")
                    
        else:
            print(f"Found {len(students)} students already")
            
        # Final count
        final_students = db.query(Student).all()
        final_grades = db.query(Grade).all()
        print(f"Total students: {len(final_students)}")
        print(f"Total grades: {len(final_grades)}")
        
        # Show breakdown by section
        for section in sections:
            section_students = db.query(Student).filter(Student.section_id == section.id).all()
            print(f"{section.name}: {len(section_students)} students")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()