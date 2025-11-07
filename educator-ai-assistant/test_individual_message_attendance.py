#!/usr/bin/env python3
"""
Test sending individual message to Jennifer WITH attendance to isolate the error
"""
import requests
import json

def test_individual_message_with_attendance():
    """Test sending individual message to Jennifer with attendance field"""
    
    print("📧 Testing Individual Message to Jennifer (With Attendance)")
    print("=" * 60)
    
    try:
        # Login as Ananya
        login_response = requests.post("http://localhost:8003/api/v1/educators/login", data={
            "username": "ananya.rao@school.com",
            "password": "Ananya@123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Logged in as Ananya Rao")
        
        # Send individual message to Jennifer WITH ATTENDANCE FIELD
        message_data = {
            "target_type": "individual",
            "student_emails": ["jennifer.colon@student.edu"],
            "subject": "🧪 Test Message with Attendance",
            "message_template": """Dear {student_name},

This is a test message with attendance.

📚 Your Details:
• Section: {section}
• Roll Number: {roll_no}
• Grade: {grade_letter}
• Attendance: {attendance_percentage}%

Best regards,
Ananya Rao""",
            "send_email": False,
            "create_notifications": True,
            "selected_template": "performance_report"
        }
        
        print("📤 Sending individual message to Jennifer...")
        response = requests.post(
            "http://localhost:8003/api/v1/bulk-communication/bulk-email",
            headers=headers,
            json=message_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Message sent successfully!")
            print(f"📊 Status: {result['message']}")
            print(f"🔔 Notifications: {result['notifications_created']}")
            print(f"📧 Email results: {len(result.get('email_results', []))}")
            
            # Show any errors
            for email_result in result.get('email_results', []):
                if not email_result['success']:
                    print(f"❌ Error for {email_result['student_email']}: {email_result['message']}")
                else:
                    print(f"✅ Success for {email_result['student_email']}: {email_result['message']}")
            
            # Check performance data
            if result.get('performance_data'):
                for perf in result['performance_data']:
                    if 'jennifer' in perf['student_name'].lower():
                        print(f"📊 Jennifer's Performance Data:")
                        print(f"   Name: {perf['student_name']}")
                        print(f"   Roll: {perf['roll_no']}")
                        print(f"   Average: {perf['average_score']}%")
                        print(f"   Attendance: {perf.get('attendance_percentage', 'NOT_FOUND')}%")
                        break
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Attendance Message Test Complete!")

if __name__ == "__main__":
    test_individual_message_with_attendance()