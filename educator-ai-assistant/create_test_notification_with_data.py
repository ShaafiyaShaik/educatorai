#!/usr/bin/env python3
"""
Create a test notification with structured report data to test View Report functionality
"""
import sqlite3
import json
from datetime import datetime

def create_test_notification():
    try:
        # Connect to the database
        conn = sqlite3.connect('educator_db.sqlite')
        cursor = conn.cursor()
        
        # Sample structured report data matching the expected format
        report_data = {
            "student_name": "Rahul Sharma",
            "roll_no": "S101",
            "section": "Mathematics Section A",
            "report_date": datetime.now().strftime("%d/%m/%Y"),
            "subjects": {
                "Mathematics": 81.0,
                "Science": 59.0,
                "English": 0.0
            },
            "overall": {
                "average": 70.0,
                "grade": "B",
                "status": "Pass"
            },
            "educator_name": "Ananya Rao"
        }
        
        # Insert test notification
        cursor.execute("""
            INSERT INTO Notifications 
            (educator_id, student_id, title, message, notification_type, status, additional_data, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,  # educator_id (Ananya)
            1,  # student_id (Rahul)
            "Test Academic Performance Report - With Structured Data",
            "This is a test notification with structured report data for testing the View Report button functionality.",
            "GRADE_REPORT",
            "UNREAD",
            json.dumps(report_data),
            datetime.now().isoformat()
        ))
        
        # Commit the changes
        conn.commit()
        
        # Get the inserted notification
        cursor.execute("SELECT id FROM Notifications WHERE title = ? ORDER BY created_at DESC LIMIT 1", 
                      ("Test Academic Performance Report - With Structured Data",))
        notification_id = cursor.fetchone()[0]
        
        print(f"✅ Test notification created successfully!")
        print(f"Notification ID: {notification_id}")
        print(f"Report Data: {json.dumps(report_data, indent=2)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_test_notification()