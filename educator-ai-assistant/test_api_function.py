#!/usr/bin/env python3
"""
Test the exact API function that's failing
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.api.students import get_filtered_section_students
from fastapi import HTTPException

async def test_api_function():
    db = next(get_db())
    
    # Get the educator
    educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    
    if educator:
        print(f"Testing with educator: {educator.full_name}")
        
        try:
            # Call the actual API function
            result = await get_filtered_section_students(
                section_id=6,
                pass_status=None,
                subject_filter=None,
                search=None,
                current_educator=educator,
                db=db
            )
            
            print(f"SUCCESS: Found {len(result)} students")
            if result:
                student = result[0]
                print(f"First student: {student.full_name}, average: {student.overall_average}")
                
        except Exception as e:
            print(f"ERROR in API function: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api_function())