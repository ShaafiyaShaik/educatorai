#!/usr/bin/env python3
"""
Test sending individual message to Jennifer to check notification creation
"""
import requests
import json

def test_individual_message():
    """Test sending individual message to Jennifer"""
    
    print("📧 Testing Individual Message to Jennifer")
    print("=" * 50)
    
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
        
        # Send individual message to Jennifer
        message_data = {
            "target_type": "individual",
            "student_emails": ["jennifer.colon@student.edu"],
            "subject": "🧪 Test Individual Message with Performance Data",
            "message_template": """Dear {student_name},

This is a test message to verify dashboard notifications work correctly.

📚 Your Academic Details:
• Section: {section}
• Roll Number: {roll_no}
• Overall Average: {average_score}%
• Grade: {grade_letter}
• Status: {status}
• Attendance: {attendance_percentage}%

This message should appear in your dashboard notifications.

Best regards,
Ananya Rao""",
            "send_email": False,
            "create_notifications": True,
            "selected_template": "performance_report"
        }
        
        print("📤 Sending individual message to Jennifer...")
        
        response = requests.post(
            "http://localhost:8003/api/v1/bulk-communication/bulk-email",
            json=message_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Message sent successfully!")
            print(f"📊 Status: {result['message']}")
            print(f"🔔 Notifications: {result['notifications_created']}")
            print(f"📧 Email results: {len(result['email_results'])}")
            
            # Check for errors in email results
            for email_result in result['email_results']:
                if not email_result['success']:
                    print(f"❌ Error for {email_result['student_email']}: {email_result['message']}")
                else:
                    print(f"✅ Success for {email_result['student_email']}: {email_result['message']}")
            
            # Show performance data
            if result['performance_data']:
                perf = result['performance_data'][0]
                print(f"\n📊 Jennifer's Performance Data:")
                print(f"   Name: {perf['student_name']}")
                print(f"   Roll: {perf['roll_no']}")
                print(f"   Average: {perf['average_score']}%")
                print(f"   Attendance: {perf['attendance_percentage']}%")
        else:
            print(f"❌ Message failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"\n{'='*50}")
    print("🏁 Individual Message Test Complete!")

if __name__ == "__main__":
    test_individual_message()