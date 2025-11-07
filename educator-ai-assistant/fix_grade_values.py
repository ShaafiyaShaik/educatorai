#!/usr/bin/env python3
"""
Fix grades that have None values for grade_letter and is_passed
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Grade, Subject

def fix_grade_values():
    db = next(get_db())
    
    print("=== Fixing Grade Values ===")
    
    # Get all grades with None values
    grades_with_none = db.query(Grade).filter(
        (Grade.grade_letter.is_(None)) | (Grade.is_passed.is_(None))
    ).all()
    
    print(f"Found {len(grades_with_none)} grades with None values")
    
    for grade in grades_with_none:
        print(f"Fixing grade {grade.id}: {grade.percentage}%")
        
        # Calculate percentage if not set
        if grade.percentage is None:
            grade.calculate_percentage()
        
        # Calculate grade letter
        grade.calculate_grade_letter()
        
        # Get the subject's passing grade to determine if passed
        subject = db.query(Subject).filter(Subject.id == grade.subject_id).first()
        if subject:
            grade.is_passed = grade.percentage >= subject.passing_grade
        else:
            grade.is_passed = grade.percentage >= 60  # Default passing grade
        
        print(f"  Updated: {grade.percentage}% -> {grade.grade_letter}, Passed: {grade.is_passed}")
    
    # Commit the changes
    db.commit()
    print(f"Fixed {len(grades_with_none)} grades")
    
    # Verify the fix
    remaining_none = db.query(Grade).filter(
        (Grade.grade_letter.is_(None)) | (Grade.is_passed.is_(None))
    ).count()
    
    print(f"Remaining grades with None values: {remaining_none}")
    
    db.close()

if __name__ == "__main__":
    fix_grade_values()