#!/usr/bin/env python3
"""
Create sample grade data for the students we just created
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

def create_sample_grades():
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'educator_assistant.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Creating sample grades...")
    
    # Get all students and their sections
    cursor.execute("""
        SELECT s.id, s.first_name, s.last_name, s.section_id, sec.name as section_name, sec.educator_id
        FROM students s
        JOIN sections sec ON s.section_id = sec.id
        WHERE s.email LIKE 'student%@school.edu'
    """)
    students = cursor.fetchall()
    
    # Grade types and their weights
    grade_types = [
        ('Quiz', 0.2),
        ('Assignment', 0.3),
        ('Test', 0.3), 
        ('Project', 0.2)
    ]
    
    # Subjects based on section names
    subject_mapping = {
        'Math': ['Algebra', 'Geometry', 'Statistics'],
        'Science': ['Biology', 'Chemistry', 'Physics'],
        'English': ['Literature', 'Grammar', 'Writing'],
        'Biology': ['Cell Biology', 'Genetics', 'Ecology'],
        'Literature': ['Poetry', 'Novels', 'Drama']
    }
    
    grade_count = 0
    
    for student in students:
        student_id, first_name, last_name, section_id, section_name, educator_id = student
        
        # Determine subject from section name
        subject = 'General'
        for key in subject_mapping:
            if key in section_name:
                subject = key
                break
        
        # Create 5-8 grades per student
        num_grades = random.randint(5, 8)
        
        for i in range(num_grades):
            # Random grade type
            grade_type, weight = random.choice(grade_types)
            
            # Random score between 65-95
            score = random.randint(65, 95)
            
            # Random date within last 2 months
            days_ago = random.randint(1, 60)
            grade_date = datetime.now() - timedelta(days=days_ago)
            
            # Random topic
            topics = subject_mapping.get(subject, ['Topic A', 'Topic B', 'Topic C'])
            topic = random.choice(topics)
            
            try:
                cursor.execute("""
                    INSERT INTO grades 
                    (student_id, marks_obtained, total_marks, percentage, grade_letter, is_passed, 
                     assessment_type, assessment_date, remarks, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_id,
                    score,
                    100,  # total_marks
                    (score/100)*100,  # percentage
                    'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D',
                    score >= 60,  # is_passed
                    grade_type,
                    grade_date.isoformat(),
                    f"Good work on {topic.lower()}!" if score >= 80 else "Needs improvement",
                    datetime.now().isoformat()
                ))
                grade_count += 1
                
            except Exception as e:
                print(f"❌ Error creating grade for {first_name} {last_name}: {e}")
        
        print(f"  ✅ Created {num_grades} grades for {first_name} {last_name}")
    
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM grades WHERE created_at >= date('now', '-1 day')")
    total_grades = cursor.fetchone()[0]
    
    print(f"\n📊 Created {total_grades} grade records!")
    
    # Show sample data
    cursor.execute("""
        SELECT s.first_name, s.last_name, g.assessment_type, g.marks_obtained, g.total_marks, g.grade_letter
        FROM grades g
        JOIN students s ON g.student_id = s.id
        WHERE g.created_at >= date('now', '-1 day')
        LIMIT 10
    """)
    
    print("\n📋 Sample Grade Records:")
    for row in cursor.fetchall():
        name, lastname, assessment, marks, total, grade = row
        percentage = (marks/total)*100
        print(f"  {name} {lastname}: {assessment} - {marks}/{total} ({percentage:.1f}%) Grade: {grade}")
    
    conn.close()

if __name__ == "__main__":
    create_sample_grades()