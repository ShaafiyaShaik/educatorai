#!/usr/bin/env python3
"""
Test the PDF generation function directly
"""

from app.core.database import SessionLocal
from app.models.educator import Educator

def test_pdf_generation():
    """Test PDF generation function directly"""
    try:
        # Import here to catch any import errors
        from app.api.performance_views import generate_pdf_report
        
        # Get database and educator
        db = SessionLocal()
        educator = db.query(Educator).filter(Educator.email == 'shaaf@gmail.com').first()
        
        if not educator:
            print("❌ Educator not found")
            return False
        
        print(f"✅ Found educator: {educator.email}")
        
        # Test PDF generation
        print("🔄 Generating PDF report...")
        
        # Call the function (it's async, so we need to use asyncio)
        import asyncio
        
        async def test_async():
            try:
                result = await generate_pdf_report("overall", None, None, educator, db)
                print(f"✅ PDF generated successfully: {result}")
                return True
            except Exception as e:
                print(f"❌ PDF generation failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Run the async function
        return asyncio.run(test_async())
        
    except Exception as e:
        print(f"❌ Error in test setup: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🔍 Testing PDF Generation Function...")
    success = test_pdf_generation()
    if success:
        print("🎉 PDF test successful!")
    else:
        print("❌ PDF test failed!")