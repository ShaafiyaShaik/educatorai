#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.database import SessionLocal
    from app.models.student import Student
    from app.models.notification import Notification, NotificationType, NotificationStatus
    from datetime import datetime
    
    print("🔔 Creating test notifications...")
    
    db = SessionLocal()
    
    # Find Rahul
    student = db.query(Student).filter(Student.email == "rahul.s101@school.com").first()
    if not student:
        print("❌ Student not found")
        exit(1)
        
    print(f"✅ Found student: {student.full_name}")
    
    # Create test notification
    notification = Notification(
        student_id=student.id,
        title="Test Message from Ananya Rao",
        message="Subject: attendance report\n\nYour attendance is low! Meet me this instant.",
        notification_type=NotificationType.COMMUNICATION,
        status=NotificationStatus.UNREAD,
        priority="normal",
        category="communication",
        created_at=datetime.utcnow()
    )
    
    db.add(notification)
    db.commit()
    
    print(f"✅ Created notification ID: {notification.id}")
    
    # Check how many notifications exist for this student
    count = db.query(Notification).filter(Notification.student_id == student.id).count()
    print(f"📊 Total notifications for {student.full_name}: {count}")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()