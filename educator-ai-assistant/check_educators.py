#!/usr/bin/env python3
"""
Check available educators in the database
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator

def check_educators():
    """Check what educators exist in the database"""
    
    print("🔍 CHECKING AVAILABLE EDUCATORS")
    print("=" * 40)
    
    db = next(get_db())
    
    try:
        educators = db.query(Educator).all()
        
        if not educators:
            print("❌ No educators found in database")
            return None
            
        print(f"✅ Found {len(educators)} educators:")
        for i, educator in enumerate(educators, 1):
            print(f"   {i}. {educator.email} - {educator.full_name}")
        
        # Return the first educator for testing
        return educators[0]
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    educator = check_educators()
    if educator:
        print(f"\n🎯 Using '{educator.email}' for testing")
    else:
        print("\n⚠️  Need to create test educator first")