#!/usr/bin/env python3
"""
Test API directly without server - check exact calculation logic
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.models.student import Section, Student, Grade, Subject
from app.api.performance_views import get_overall_performance
import asyncio

async def debug_api_calculation():
    db = next(get_db())
    
    print("🔍 DEBUGGING PERFORMANCE API CALCULATION")
    print("=" * 60)
    
    # Get Shaaf
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    print(f"Educator: {shaaf.first_name} {shaaf.last_name} (ID: {shaaf.id})")
    
    # Check raw data
    sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    print(f"\n📚 Sections ({len(sections)}):")
    
    total_grades = 0
    total_score = 0
    
    for section in sections:
        students = db.query(Student).filter(Student.section_id == section.id).all()
        
        # Get grades for this section
        section_grades = db.query(Grade).join(Student).filter(
            Student.section_id == section.id
        ).all()
        
        section_total = sum(g.percentage for g in section_grades if g.percentage is not None)
        section_count = len([g for g in section_grades if g.percentage is not None])
        section_avg = section_total / section_count if section_count > 0 else 0
        
        print(f"  {section.name}: {len(students)} students, {section_count} grades, avg: {section_avg:.1f}")
        
        total_grades += section_count
        total_score += section_total
    
    overall_avg = total_score / total_grades if total_grades > 0 else 0
    print(f"\n🧮 Manual Calculation:")
    print(f"  Total grades: {total_grades}")
    print(f"  Total score: {total_score}")
    print(f"  Manual average: {overall_avg:.1f}%")
    
    # Now test the API function
    try:
        print(f"\n🚀 Testing API Function...")
        result = await get_overall_performance(current_educator=shaaf, db=db)
        
        print(f"\n📊 API RESULTS:")
        print(f"  API Average: {result.overall_average:.1f}%")
        print(f"  API Pass Rate: {result.overall_pass_rate:.1f}%")
        print(f"  API Total Students: {result.total_students}")
        print(f"  API Total Sections: {result.total_sections}")
        
        # Compare
        print(f"\n🔍 COMPARISON:")
        print(f"  Manual vs API Average: {overall_avg:.1f}% vs {result.overall_average:.1f}%")
        if abs(overall_avg - result.overall_average) < 0.1:
            print("  ✅ Calculations match!")
        else:
            print("  ❌ Calculations don't match!")
        
        # Check if sections_summary has data
        if hasattr(result, 'sections_summary') and result.sections_summary:
            print(f"\n📋 Sections Summary ({len(result.sections_summary)}):")
            for i, section_perf in enumerate(result.sections_summary):
                print(f"  {i+1}. {section_perf.section_name}: {section_perf.average_score:.1f}% ({section_perf.total_students} students)")
        
    except Exception as e:
        print(f"❌ API ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_api_calculation())