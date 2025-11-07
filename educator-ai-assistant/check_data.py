from app.core.database import SessionLocal
from app.models.student import Student, Section, Grade, Subject
from app.models.educator import Educator

db = SessionLocal()

try:
    educator = db.query(Educator).filter(Educator.email == 'shaaf@gmail.com').first()
    if educator:
        print(f'Educator: {educator.email} (ID: {educator.id})')
        
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f'Sections: {len(sections)}')
        for section in sections:
            print(f'  - {section.name} (ID: {section.id})')
        
        students = db.query(Student).join(Section).filter(Section.educator_id == educator.id).all()
        print(f'Students: {len(students)}')
        
        grades = db.query(Grade).join(Student).join(Section).filter(Section.educator_id == educator.id).all()
        print(f'Grades: {len(grades)}')
    else:
        print('No educator found')
finally:
    db.close()