#!/usr/bin/env python3
"""
Test performance API directly to find the issue
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.models.student import Section, Student, Grade, Subject
from app.api.performance_views import get_overall_performance
import asyncio

async def debug_performance_api():
    db = next(get_db())
    
    print("🔍 DEBUGGING PERFORMANCE API")
    print("=" * 50)
    
    # Get Shaaf
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    print(f"Shaaf ID: {shaaf.id}")
    
    # Check sections and students
    sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    print(f"Shaaf's sections: {len(sections)}")
    
    for section in sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        grade_count = db.query(Grade).join(Student).filter(Student.section_id == section.id).count()
        print(f"  {section.name}: {student_count} students, {grade_count} grades")
    
    # Test the API function
    try:
        print(f"\n🧮 Calling get_overall_performance...")
        result = await get_overall_performance(current_educator=shaaf, db=db)
        
        print(f"\n📊 API RESULTS:")
        print(f"  Total sections: {result.total_sections}")
        print(f"  Total students: {result.total_students}")
        print(f"  Total subjects: {result.total_subjects}")
        print(f"  Overall average: {result.overall_average}%")
        print(f"  Pass rate: {result.overall_pass_rate}%")
        
        if result.overall_average == 0:
            print(f"\n❌ PROBLEM FOUND: Overall average is 0!")
            print(f"Let's debug the sections summary...")
            
            for i, section_perf in enumerate(result.sections_summary):
                print(f"\n  Section {i+1}: {section_perf.section_name}")
                print(f"    Total students: {section_perf.total_students}")
                print(f"    Average score: {section_perf.average_score}")
                print(f"    Pass rate: {section_perf.pass_rate}%")
                
                if section_perf.average_score == 0:
                    print(f"    ❌ This section has 0 average!")
        
        print(f"\n📈 Grade Level Stats:")
        stats = result.grade_level_stats
        print(f"  Excellent (90%+): {stats.get('excellent', 0)}")
        print(f"  Good (75-89%): {stats.get('good', 0)}")
        print(f"  Average (60-74%): {stats.get('average', 0)}")
        print(f"  Below Average (<60%): {stats.get('below_average', 0)}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_performance_api())