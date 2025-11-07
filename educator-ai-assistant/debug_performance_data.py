"""
Debug Performance Data Issues
Check what data the API is returning and identify calculation problems
"""

import requests
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.student import Student, Grade, Subject, Section
from app.models.educator import Educator

def check_raw_data():
    """Check what data exists in the database"""
    db = next(get_db())
    
    try:
        print("🔍 CHECKING RAW DATABASE DATA")
        print("=" * 50)
        
        # Check students
        students = db.query(Student).all()
        print(f"📊 Total Students: {len(students)}")
        
        if students:
            for i, student in enumerate(students[:5]):
                full_name = f"{student.first_name} {student.last_name}"
                print(f"   {i+1}. {full_name} (ID: {student.id}, Section: {student.section_id})")
        
        # Check grades
        grades = db.query(Grade).all()
        print(f"📊 Total Grades: {len(grades)}")
        
        if grades:
            for i, grade in enumerate(grades[:5]):
                subject_name = grade.subject.name if grade.subject else "Unknown"
                print(f"   {i+1}. Student ID: {grade.student_id}, Subject: {subject_name}, Score: {grade.marks_obtained}, Total: {grade.total_marks}")
        
        # Check subjects
        subjects = db.query(Subject).all()
        print(f"📊 Total Subjects: {len(subjects)}")
        
        if subjects:
            for i, subject in enumerate(subjects):
                print(f"   {i+1}. {subject.name} (Code: {subject.code})")
        
        # Check sections
        sections = db.query(Section).all()
        print(f"📊 Total Sections: {len(sections)}")
        
        if sections:
            for i, section in enumerate(sections):
                student_count = db.query(Student).filter(Student.section_id == section.id).count()
                print(f"   {i+1}. {section.name} (ID: {section.id}, Students: {student_count})")
        
        # Check educators
        educators = db.query(Educator).all()
        print(f"📊 Total Educators: {len(educators)}")
        
        if educators:
            for i, educator in enumerate(educators):
                full_name = f"{educator.first_name} {educator.last_name}"
                print(f"   {i+1}. {full_name} (ID: {educator.id}, Email: {educator.email})")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_api_response():
    """Check what the performance API is returning"""
    print("\n🔍 CHECKING API RESPONSES")
    print("=" * 50)
    
    base_url = "http://localhost:8003"
    
    # Test login first
    print("1. Testing login...")
    login_data = {
        "username": "shaaf",
        "password": "shaaf123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data, timeout=10)
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
            
            # Test overview endpoint
            print("\n2. Testing /api/v1/performance/overview...")
            try:
                response = requests.get(f"{base_url}/api/v1/performance/overview", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Overview API Response:")
                    print(f"   Total Students: {data.get('total_students')}")
                    print(f"   Total Sections: {data.get('total_sections')}")
                    print(f"   Total Subjects: {data.get('total_subjects')}")
                    print(f"   Overall Average: {data.get('overall_average')}")
                    print(f"   Overall Pass Rate: {data.get('overall_pass_rate')}")
                    
                    # Check sections summary
                    sections_summary = data.get('sections_summary', [])
                    print(f"   Sections Summary Count: {len(sections_summary)}")
                    
                    if sections_summary:
                        print("   First Section Details:")
                        section = sections_summary[0]
                        print(f"     Name: {section.get('section_name')}")
                        print(f"     Total Students: {section.get('total_students')}")
                        print(f"     Average Score: {section.get('average_score')}")
                        print(f"     Pass Rate: {section.get('pass_rate')}")
                    
                    # Check subjects summary
                    subjects_summary = data.get('subjects_summary', [])
                    print(f"   Subjects Summary Count: {len(subjects_summary)}")
                    
                    if subjects_summary:
                        print("   First Subject Details:")
                        subject = subjects_summary[0]
                        print(f"     Name: {subject.get('subject_name')}")
                        print(f"     Total Students: {subject.get('total_students')}")
                        print(f"     Average Score: {subject.get('average_score')}")
                        print(f"     Pass Rate: {subject.get('pass_rate')}")
                    
                    # Check grade distribution
                    grade_dist = data.get('grade_distribution', {})
                    print(f"   Grade Distribution: {grade_dist}")
                    
                else:
                    print(f"❌ Overview API failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ API request error: {e}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Is the server running on localhost:8003?")

def calculate_grades_manually():
    """Manually calculate what the grades should be"""
    db = next(get_db())
    
    try:
        print("\n🧮 MANUAL GRADE CALCULATIONS")
        print("=" * 50)
        
        # Get all grades with students and subjects
        grades = db.query(Grade).join(Student).join(Subject).all()
        
        if not grades:
            print("❌ No grades found in database!")
            return
        
        total_scores = []
        student_averages = {}
        subject_averages = {}
        
        for grade in grades:
            if grade.marks_obtained is not None and grade.total_marks is not None and grade.total_marks > 0:
                percentage = (grade.marks_obtained / grade.total_marks) * 100
                total_scores.append(percentage)
                
                # Student averages
                student_id = grade.student_id
                if student_id not in student_averages:
                    student_averages[student_id] = []
                student_averages[student_id].append(percentage)
                
                # Subject averages  
                subject_name = grade.subject.name if grade.subject else "Unknown"
                if subject_name not in subject_averages:
                    subject_averages[subject_name] = []
                subject_averages[subject_name].append(percentage)
        
        if total_scores:
            overall_average = sum(total_scores) / len(total_scores)
            pass_count = sum(1 for score in total_scores if score >= 60)
            pass_rate = (pass_count / len(total_scores)) * 100
            
            print(f"📊 Manual Calculations:")
            print(f"   Total Grade Records: {len(total_scores)}")
            print(f"   Overall Average: {overall_average:.2f}%")
            print(f"   Pass Rate: {pass_rate:.2f}%")
            print(f"   Students with Grades: {len(student_averages)}")
            print(f"   Subjects with Grades: {len(subject_averages)}")
            
            # Show student averages
            print(f"\n📚 Student Averages (first 5):")
            for i, (student_id, scores) in enumerate(list(student_averages.items())[:5]):
                avg = sum(scores) / len(scores)
                student = db.query(Student).filter(Student.id == student_id).first()
                student_name = f"{student.first_name} {student.last_name}" if student else f"Student {student_id}"
                print(f"   {student_name}: {avg:.2f}% (from {len(scores)} grades)")
                
        else:
            print("❌ No valid grade data found for calculations!")
        
    except Exception as e:
        print(f"❌ Error in manual calculations: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    print("🚨 DEBUGGING PERFORMANCE DATA ISSUES")
    print("🔧 Checking database content, API responses, and calculations")
    print("\n")
    
    # Step 1: Check raw database data
    check_raw_data()
    
    # Step 2: Manual calculations
    calculate_grades_manually()
    
    # Step 3: Check API responses
    check_api_response()
    
    print("\n🎯 DEBUGGING COMPLETE!")
    print("Look for issues in:")
    print("   1. Missing or invalid grade data")
    print("   2. Incorrect calculation logic in API")
    print("   3. Data mapping issues between database and API")

if __name__ == "__main__":
    main()