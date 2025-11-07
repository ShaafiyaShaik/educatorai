#!/usr/bin/env python3
"""
Test performance API directly with new data
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.api.performance_views import get_overall_performance
import asyncio

async def test_new_performance_data():
    db = next(get_db())
    
    # Get Shaaf
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    
    if shaaf:
        print(f"Testing performance for {shaaf.full_name}")
        
        try:
            # Call the performance API function directly
            result = await get_overall_performance(current_educator=shaaf, db=db)
            
            print(f"\n=== Performance Overview ===")
            print(f"Total sections: {result.total_sections}")
            print(f"Total students: {result.total_students}")
            print(f"Total subjects: {result.total_subjects}")
            print(f"Overall average: {result.overall_average:.2f}%")
            print(f"Pass rate: {result.overall_pass_rate:.2f}%")
            
            print(f"\n=== Sections Summary ===")
            for i, section in enumerate(result.sections_summary):
                print(f"  {section.section_name}: {section.total_students} students, {section.average_score:.1f}% avg")
            
            print(f"\n=== Grade Level Stats ===")
            stats = result.grade_level_stats
            print(f"  Excellent (90%+): {stats.get('excellent', 0)}")
            print(f"  Good (75-90%): {stats.get('good', 0)}")  
            print(f"  Average (60-75%): {stats.get('average', 0)}")
            print(f"  Below Average (<60%): {stats.get('below_average', 0)}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_new_performance_data())