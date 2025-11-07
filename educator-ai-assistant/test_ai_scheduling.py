#!/usr/bin/env python3
"""Test script to verify AI assistant scheduling integration with database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ai_assistant import handle_ai_assistant_command
from app.core.database import SessionLocal
from app.models.schedule import Schedule, EventType, EventStatus
from app.models.educator import Educator
from datetime import datetime, timedelta

def test_ai_scheduling():
    """Test AI assistant scheduling functionality"""
    
    print("🧪 Testing AI Assistant Scheduling Integration")
    print("=" * 50)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if we have any educator in the database
        educator = db.query(Educator).first()
        if not educator:
            print("❌ No educator found in database. Creating test educator...")
            # Create a test educator
            educator = Educator(
                first_name="Test",
                last_name="Teacher",
                email="test@school.edu",
                hashed_password="test_password",
                department="Math Department",
                title="Professor"
            )
            db.add(educator)
            db.commit()
            print(f"✅ Created test educator: {educator.first_name} {educator.last_name} (ID: {educator.id})")
        else:
            print(f"✅ Using existing educator: {educator.first_name} {educator.last_name} (ID: {educator.id})")
        
        # Test 1: Parent Meeting Scheduling
        print("\n🧪 Test 1: Parent Meeting Scheduling")
        print("-" * 30)
        
        # Step 1: Initiate parent meeting request
        response1 = handle_ai_assistant_command(
            "I need to schedule a parent meeting", 
            educator_id=educator.id
        )
        print(f"Step 1 Response: {response1.response_text[:100]}...")
        
        # Step 2: Provide student name
        response2 = handle_ai_assistant_command(
            "John Smith", 
            educator_id=educator.id
        )
        print(f"Step 2 Response: {response2.response_text[:100]}...")
        
        # Step 3: Provide timing
        response3 = handle_ai_assistant_command(
            "Tomorrow morning at 10:00 AM for academic discussion", 
            educator_id=educator.id
        )
        print(f"Step 3 Response: {response3.response_text[:100]}...")
        
        # Step 4: Confirm
        response4 = handle_ai_assistant_command(
            "yes, book it", 
            educator_id=educator.id
        )
        print(f"Step 4 Response: {response4.response_text[:100]}...")
        
        # Check if meeting was created in database
        parent_meetings = db.query(Schedule).filter(
            Schedule.educator_id == educator.id,
            Schedule.title.like('%Parent Meeting%')
        ).all()
        
        if parent_meetings:
            meeting = parent_meetings[-1]  # Get the latest one
            print(f"✅ Parent meeting created in database!")
            print(f"   Title: {meeting.title}")
            print(f"   Date: {meeting.start_datetime}")
            print(f"   Status: {meeting.status}")
        else:
            print("❌ Parent meeting not found in database")
        
        # Test 2: Staff Meeting Scheduling
        print("\n🧪 Test 2: Staff Meeting Scheduling")
        print("-" * 30)
        
        # Step 1: Initiate staff meeting request
        response1 = handle_ai_assistant_command(
            "I need to schedule a staff meeting", 
            educator_id=educator.id
        )
        print(f"Step 1 Response: {response1.response_text[:100]}...")
        
        # Step 2: Provide timing
        response2 = handle_ai_assistant_command(
            "Tomorrow afternoon at 3:00 PM", 
            educator_id=educator.id
        )
        print(f"Step 2 Response: {response2.response_text[:100]}...")
        
        # Step 3: Confirm
        response3 = handle_ai_assistant_command(
            "yes", 
            educator_id=educator.id
        )
        print(f"Step 3 Response: {response3.response_text[:100]}...")
        
        # Check if meeting was created in database
        staff_meetings = db.query(Schedule).filter(
            Schedule.educator_id == educator.id,
            Schedule.title.like('%Staff Meeting%')
        ).all()
        
        if staff_meetings:
            meeting = staff_meetings[-1]  # Get the latest one
            print(f"✅ Staff meeting created in database!")
            print(f"   Title: {meeting.title}")
            print(f"   Date: {meeting.start_datetime}")
            print(f"   Status: {meeting.status}")
        else:
            print("❌ Staff meeting not found in database")
        
        # Show all meetings for this educator
        print(f"\n📅 All Meetings for {educator.first_name} {educator.last_name}:")
        print("-" * 30)
        all_meetings = db.query(Schedule).filter(Schedule.educator_id == educator.id).all()
        for meeting in all_meetings:
            print(f"• {meeting.title} - {meeting.start_datetime.strftime('%B %d, %Y at %I:%M %p')}")
        
        print(f"\n✅ Test completed! Total meetings in database: {len(all_meetings)}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_scheduling()