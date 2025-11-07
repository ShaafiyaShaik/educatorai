#!/usr/bin/env python3
"""
Check database for student data and grades
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.database import get_db
from app.models.student import Student, Grade
from app.models.educator import Educator
from sqlalchemy import func

def check_database():
    """Check database for student data"""
    db = next(get_db())
    
    try:
        # Check educator
        educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        if not educator:
            print("❌ Educator shaaf@gmail.com not found")
            return
            
        print(f"✅ Found educator: {educator.name} (ID: {educator.id})")
        
        # Check students
        student_count = db.query(Student).count()
        print(f"📊 Total students in database: {student_count}")
        
        # Check grades
        grade_count = db.query(Grade).count()
        print(f"📝 Total grades in database: {grade_count}")
        
        if grade_count > 0:
            # Sample grades
            sample_grades = db.query(Grade).limit(5).all()
            print(f"📋 Sample grades:")
            for grade in sample_grades:
                print(f"   Student {grade.student_id}: {grade.score}/100 in subject {grade.subject_id}")
                
        # Check students with grades
        students_with_grades = db.query(Student).join(Grade).filter(
            Student.section_id.in_(
                db.query(func.distinct(Student.section_id)).filter(
                    Student.section_id != None
                ).subquery().c.section_id
            )
        ).count()
        
        print(f"👥 Students with grades: {students_with_grades}")
        
        # Check average scores
        if grade_count > 0:
            avg_score = db.query(func.avg(Grade.score)).scalar()
            print(f"📈 Average score across all grades: {avg_score:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Checking database for student performance data...")
    check_database()
    print("✨ Check completed!")