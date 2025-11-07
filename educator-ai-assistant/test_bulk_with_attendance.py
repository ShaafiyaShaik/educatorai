#!/usr/bin/env python3
"""
Test sending a bulk message with corrected performance data and attendance
"""
import requests
import json

def test_bulk_message_with_attendance():
    """Test sending bulk message to verify corrected data includes attendance"""
    
    print("📨 Testing Bulk Message with Corrected Performance & Attendance")
    print("=" * 70)
    
    # Login as Ananya
    login_response = requests.post("http://localhost:8000/api/v1/educators/login", json={
        "email": "ananya.rao@school.com",
        "password": "Ananya@123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Logged in as Ananya Rao")
    
    # Send bulk message to Mathematics Section A (includes Jennifer)
    bulk_data = {
        "target_type": "section",
        "sections": ["Mathematics Section A"],
        "subject": "📊 Updated Academic Performance Report with Attendance",
        "message_template": """Dear {student_name},

Your updated academic performance report is now available with attendance tracking:

📚 Section: {section}
🆔 Roll Number: {roll_no}

📊 Academic Performance:
• Mathematics: {math_marks}%
• Science: {science_marks}%
• English: {english_marks}%
• Overall Average: {average_score}%
• Grade: {grade_letter}
• Status: {status}

🎯 Attendance: {attendance_percentage}%

This report now includes your complete attendance record and matches your dashboard data exactly.

Best regards,
Ananya Rao
Mathematics Teacher""",
        "send_email": False,
        "create_notifications": True,
        "selected_template": "performance_report"
    }
    
    print("📤 Sending bulk message with performance and attendance data...")
    
    bulk_response = requests.post(
        "http://localhost:8000/api/v1/bulk-communication/bulk-email",
        json=bulk_data,
        headers=headers
    )
    
    if bulk_response.status_code == 200:
        result = bulk_response.json()
        print("✅ Bulk message sent successfully!")
        print(f"📊 Message: {result['message']}")
        print(f"🔔 Notifications created: {result['notifications_created']}")
        
        # Show Jennifer's performance data from the response
        if result['performance_data']:
            jennifer_data = None
            for student in result['performance_data']:
                if 'Jennifer' in student['student_name']:
                    jennifer_data = student
                    break
            
            if jennifer_data:
                print(f"\n👤 Jennifer's Data in Bulk Report:")
                print(f"   📊 Average: {jennifer_data['average_score']}%")
                print(f"   🎓 Grade: {jennifer_data['grade_letter']}")
                print(f"   ✅ Status: {jennifer_data['status']}")
                print(f"   📚 Mathematics: {jennifer_data['math_marks']}%")
                print(f"   🧪 Science: {jennifer_data['science_marks']}%")
                print(f"   📖 English: {jennifer_data['english_marks']}%")
                print(f"   🎯 Attendance: {jennifer_data['attendance_percentage']}%")
                
                print(f"\n🎯 Verification:")
                expected_avg = 63.5  # From our test
                actual_avg = jennifer_data['average_score']
                match = abs(expected_avg - actual_avg) < 0.1
                print(f"   Average matches dashboard: {'✅' if match else '❌'} ({actual_avg}% vs {expected_avg}%)")
                print(f"   Attendance included: {'✅' if 'attendance_percentage' in jennifer_data else '❌'}")
                
    else:
        print(f"❌ Bulk message failed: {bulk_response.status_code}")
        print(f"Response: {bulk_response.text}")
    
    print(f"\n{'='*70}")
    print("🏁 Bulk Message Test Complete!")

if __name__ == "__main__":
    test_bulk_message_with_attendance()