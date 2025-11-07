#!/usr/bin/env python3
"""
Check what the API actually returns for notifications
"""
import sqlite3
import json

def check_notification_data():
    try:
        # Connect to the database
        conn = sqlite3.connect('educator_db.sqlite')
        cursor = conn.cursor()
        
        # Get the test notification I created
        cursor.execute("""
            SELECT id, title, notification_type, additional_data 
            FROM Notifications 
            WHERE title = 'Test Academic Performance Report - With Structured Data'
        """)
        
        result = cursor.fetchone()
        if result:
            notification_id, title, notification_type, additional_data = result
            print(f"Notification ID: {notification_id}")
            print(f"Title: {title}")
            print(f"Type: {notification_type}")
            print(f"Additional Data: {additional_data}")
            
            if additional_data:
                try:
                    parsed_data = json.loads(additional_data)
                    print(f"Parsed Data: {json.dumps(parsed_data, indent=2)}")
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
            else:
                print("No additional_data found")
        else:
            print("Test notification not found")
            
        # Also check all notifications for student ID 1
        cursor.execute("""
            SELECT id, title, notification_type, additional_data IS NOT NULL as has_data
            FROM Notifications 
            WHERE student_id = 1 
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        print("\nAll notifications for student 1:")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Title: {row[1]}, Type: {row[2]}, Has Data: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_notification_data()