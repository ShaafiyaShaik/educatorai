#!/usr/bin/env python3
"""
Test Jennifer's performance calculation to verify bulk report accuracy
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.student import Student
from app.api.bulk_communication import calculate_student_performance
from app.core.database import get_db

# Database setup
DATABASE_URL = "sqlite:///./educator_db.sqlite"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_jennifer_performance():
    """Test Jennifer's performance calculation to ensure accuracy"""
    
    print("🧪 Testing Jennifer's Performance Calculation")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Find Jennifer Colon
        jennifer = db.query(Student).filter(
            Student.email == "jennifer.colon@student.edu"
        ).first()
        
        if not jennifer:
            print("❌ Jennifer Colon not found!")
            return
        
        print(f"✅ Found: {jennifer.first_name} {jennifer.last_name}")
        print(f"📧 Email: {jennifer.email}")
        print(f"🆔 Student ID: {jennifer.student_id}")
        print(f"📚 Section: {jennifer.section.name if jennifer.section else 'N/A'}")
        
        # Calculate performance using bulk communication method
        print(f"\n📊 Calculating Performance (Bulk Communication Method):")
        print("-" * 50)
        
        performance = calculate_student_performance(jennifer, db)
        
        print(f"📈 Overall Average: {performance.average_score}%")
        print(f"🎓 Grade: {performance.grade_letter}")
        print(f"✅ Status: {performance.status}")
        print(f"📚 Subject Breakdown:")
        print(f"   • Mathematics: {performance.math_marks}%")
        print(f"   • Science: {performance.science_marks}%") 
        print(f"   • English: {performance.english_marks}%")
        print(f"🎯 Attendance: {performance.attendance_percentage}%")
        
        # Compare with detailed performance
        print(f"\n🔍 Detailed Performance Comparison:")
        print("-" * 50)
        
        from app.api.performance_views import calculate_student_performance_detailed
        detailed = calculate_student_performance_detailed(jennifer, db)
        
        print(f"📈 Detailed Average: {detailed.average_score}%")
        print(f"✅ Detailed Status: {detailed.status}")
        print(f"📚 Detailed Subject Count: {len(detailed.subject_grades)}")
        
        for i, grade in enumerate(detailed.subject_grades[:5], 1):  # Show first 5
            print(f"   {i}. {grade['subject_name']}: {grade['percentage']:.1f}%")
        
        if len(detailed.subject_grades) > 5:
            print(f"   ... and {len(detailed.subject_grades) - 5} more subjects")
        
        # Check data consistency
        print(f"\n🎯 Data Consistency Check:")
        print("-" * 50)
        
        avg_match = abs(performance.average_score - detailed.average_score) < 0.1
        status_match = performance.status == detailed.status
        
        print(f"📊 Average Match: {'✅' if avg_match else '❌'} ({performance.average_score:.1f}% vs {detailed.average_score:.1f}%)")
        print(f"✅ Status Match: {'✅' if status_match else '❌'} ({performance.status} vs {detailed.status})")
        
        if avg_match and status_match:
            print(f"\n🎉 SUCCESS! Bulk report data now matches dashboard data!")
        else:
            print(f"\n⚠️  WARNING: There are still discrepancies between bulk and dashboard data")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print(f"\n{'='*60}")
    print("🏁 Jennifer Performance Test Complete!")

if __name__ == "__main__":
    test_jennifer_performance()