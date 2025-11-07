#!/usr/bin/env python3
"""
Test PDF generation step by step to isolate the issue
"""

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def test_basic_pdf():
    """Test basic PDF creation"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Test PDF", styles['Title']))
        
        doc.build(story)
        buffer.seek(0)
        
        print("✅ Basic PDF creation works!")
        return True
        
    except Exception as e:
        print(f"❌ Basic PDF creation failed: {e}")
        return False

def test_database_access():
    """Test database access for performance data"""
    try:
        db = SessionLocal()
        
        educator = db.query(Educator).filter(Educator.email == 'shaaf@gmail.com').first()
        if not educator:
            print("❌ Educator not found")
            return False
        
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"✅ Found {len(sections)} sections")
        
        students = db.query(Student).join(Section).filter(Section.educator_id == educator.id).all()
        print(f"✅ Found {len(students)} students")
        
        grades = db.query(Grade).join(Student).join(Section).filter(Section.educator_id == educator.id).all()
        print(f"✅ Found {len(grades)} grades")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database access failed: {e}")
        return False

def test_performance_calculation():
    """Test performance calculation logic"""
    try:
        from app.api.performance_views import get_section_performance, get_subject_performance
        
        db = SessionLocal()
        educator = db.query(Educator).filter(Educator.email == 'shaaf@gmail.com').first()
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        
        if sections:
            section = sections[0]
            print(f"Testing section: {section.name}")
            
            section_perf = get_section_performance(section.id, db, educator.id)
            print(f"✅ Section performance calculated: {section_perf.total_students} students")
            
            # Test subject performance if subjects exist
            subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
            if subjects:
                subject = subjects[0]
                subject_perf = get_subject_performance(subject.id, db, educator.id)
                print(f"✅ Subject performance calculated: {subject_perf.total_students} students")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Performance calculation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing PDF Generation Components...")
    
    print("\n1. Testing Basic PDF Creation...")
    test_basic_pdf()
    
    print("\n2. Testing Database Access...")
    test_database_access()
    
    print("\n3. Testing Performance Calculations...")
    test_performance_calculation()
    
    print("\n✅ Component tests complete!")