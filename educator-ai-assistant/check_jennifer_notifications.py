#!/usr/bin/env python3
"""
Check Jennifer's notifications directly in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.student import Student
from app.models.notification import Notification
import json

# Database setup
DATABASE_URL = "sqlite:///./educator_db.sqlite"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_jennifer_notifications():
    """Check Jennifer's notifications in the database"""
    
    print("🔍 Checking Jennifer's Notifications")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Find Jennifer
        jennifer = db.query(Student).filter(
            Student.email == "jennifer.colon@student.edu"
        ).first()
        
        if not jennifer:
            print("❌ Jennifer not found!")
            return
        
        print(f"✅ Found Jennifer: ID {jennifer.id}")
        
        # Get all notifications for Jennifer
        notifications = db.query(Notification).filter(
            Notification.student_id == jennifer.id
        ).order_by(Notification.created_at.desc()).all()
        
        print(f"📊 Total notifications: {len(notifications)}")
        
        if not notifications:
            print("📭 No notifications found for Jennifer")
            return
        
        # Show each notification
        for i, notif in enumerate(notifications, 1):
            print(f"\n📋 Notification {i}:")
            print(f"   📧 Title: {notif.title}")
            print(f"   📅 Created: {notif.created_at}")
            print(f"   📖 Status: {notif.status.value}")
            print(f"   🏷️  Type: {notif.notification_type.value}")
            print(f"   💬 Message (first 100 chars): {notif.message[:100]}...")
            
            if notif.additional_data:
                try:
                    data = json.loads(notif.additional_data)
                    print(f"   📊 Additional Data Keys: {list(data.keys())}")
                    if 'overall' in data:
                        print(f"   📈 Average: {data['overall'].get('average', 'N/A')}%")
                        print(f"   🎓 Grade: {data['overall'].get('grade', 'N/A')}")
                    if 'attendance' in data:
                        print(f"   🎯 Attendance: {data['attendance'].get('percentage', 'N/A')}%")
                except:
                    print(f"   📄 Additional Data: {notif.additional_data[:50]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print(f"\n{'='*50}")
    print("🏁 Notification Check Complete!")

if __name__ == "__main__":
    check_jennifer_notifications()