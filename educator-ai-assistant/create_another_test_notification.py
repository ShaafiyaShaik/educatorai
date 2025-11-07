#!/usr/bin/env python3
"""
Create another test notification with different performance data
"""
import sqlite3
import json
from datetime import datetime

def create_another_test_notification():
    try:
        # Connect to the database
        conn = sqlite3.connect('educator_db.sqlite')
        cursor = conn.cursor()
        
        # Different test data - better performance
        report_data = {
            "student_name": "Rahul Sharma",
            "roll_no": "S101",
            "section": "Mathematics Section A",
            "report_date": datetime.now().strftime("%d/%m/%Y"),
            "subjects": {
                "Mathematics": 95.0,
                "Science": 88.0,
                "English": 92.0
            },
            "overall": {
                "average": 91.7,
                "grade": "A+",
                "status": "Pass"
            },
            "educator_name": "Ananya Rao"
        }
        
        # Insert another test notification
        cursor.execute("""
            INSERT INTO Notifications 
            (educator_id, student_id, title, message, notification_type, status, additional_data, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,  # educator_id (Ananya)
            1,  # student_id (Rahul)
            "Excellent Performance! - Quarterly Report",
            "Congratulations! Your academic performance has shown remarkable improvement. This report shows your outstanding achievements across all subjects.",
            "GRADE_REPORT",
            "UNREAD",
            json.dumps(report_data),
            datetime.now().isoformat()
        ))
        
        # Commit the changes
        conn.commit()
        
        # Get the inserted notification
        cursor.execute("SELECT id FROM Notifications WHERE title = ? ORDER BY created_at DESC LIMIT 1", 
                      ("Excellent Performance! - Quarterly Report",))
        notification_id = cursor.fetchone()[0]
        
        print(f"✅ Another test notification created successfully!")
        print(f"Notification ID: {notification_id}")
        print(f"Report Data: {json.dumps(report_data, indent=2)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_another_test_notification()