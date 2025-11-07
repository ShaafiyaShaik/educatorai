"""
Test overall performance function directly
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.api.performance_views import get_overall_performance
import asyncio

async def test_overall_performance():
    """Test the overall performance function directly"""
    db = next(get_db())
    
    # Get educator with ID 1
    educator = db.query(Educator).filter(Educator.id == 1).first()
    print(f"Testing overall performance for: {educator.full_name} ({educator.email})")
    
    try:
        # Call the function directly
        result = await get_overall_performance(current_educator=educator, db=db)
        
        print("✅ Overall performance calculation successful!")
        print(f"Total sections: {result.total_sections}")
        print(f"Total students: {result.total_students}")
        print(f"Total subjects: {result.total_subjects}")
        print(f"Overall average: {result.overall_average}%")
        print(f"Pass rate: {result.overall_pass_rate}%")
        print(f"Sections summary count: {len(result.sections_summary)}")
        print(f"Subjects summary count: {len(result.subjects_summary)}")
        print(f"Top performers count: {len(result.top_performers)}")
        print(f"Low performers count: {len(result.low_performers)}")
        
    except Exception as e:
        print(f"❌ ERROR in overall performance: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_overall_performance())