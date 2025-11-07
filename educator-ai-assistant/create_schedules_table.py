#!/usr/bin/env python3
"""
Create the schedules table if it doesn't exist
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.schedule import Schedule  # This will register the model
from app.models.student import Student, Section  
from app.models.educator import Educator
from sqlalchemy import inspect

def create_schedules_table():
    """Create schedules table if it doesn't exist"""
    print("🔧 Checking/Creating Schedules Table")
    print("=" * 50)
    
    try:
        # Check what tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"📋 Existing tables: {existing_tables}")
        
        if 'schedules' not in existing_tables:
            print("❌ Schedules table missing - creating it...")
            
            # Create all tables from Base metadata
            Base.metadata.create_all(bind=engine, checkfirst=True)
            
            # Check again
            inspector = inspect(engine)
            updated_tables = inspector.get_table_names()
            print(f"✅ Tables after creation: {updated_tables}")
            
            if 'schedules' in updated_tables:
                print("🎉 Schedules table created successfully!")
            else:
                print("❌ Failed to create schedules table")
        else:
            print("✅ Schedules table already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_schedules_table()