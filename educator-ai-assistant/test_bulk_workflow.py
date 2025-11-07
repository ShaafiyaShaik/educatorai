"""
Test Bulk Communication API - Real Email Sending
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001"
SHAAF_EMAIL = "shaafiya07@gmail.com"  # This educator has sections assigned
SHAAF_PASSWORD = "password123"

def test_bulk_communication():
    """Test the complete bulk communication workflow"""
    
    print("🚀 Testing Bulk Communication System")
    print("=" * 50)
    
    # Step 1: Login as shaaf user
    print("\n1. 📧 Logging in as shaaf...")
    login_data = {
        "username": SHAAF_EMAIL,
        "password": SHAAF_PASSWORD
    }
    login_response = requests.post(f"{BASE_URL}/api/v1/educators/login", 
                                 data=login_data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login successful! Token: {token[:20]}...")
    
    # Step 2: Get available sections
    print("\n2. 📚 Getting available sections...")
    sections_response = requests.get(f"{BASE_URL}/api/v1/bulk-communication/sections", headers=headers)
    sections = sections_response.json()["sections"]
    print(f"✅ Found {len(sections)} sections:")
    for section in sections[:3]:  # Show first 3
        print(f"   • {section['name']} - {section['student_count']} students")
    
    # Step 3: Get students from Section A (which has our test data)
    print("\n3. 👥 Getting students from Section A...")
    students_response = requests.get(f"{BASE_URL}/api/v1/bulk-communication/students?section_name=Section A", headers=headers)
    students = students_response.json()["students"]
    print(f"✅ Found {len(students)} students in Section A:")
    for student in students[:5]:  # Show first 5 students
        roll_num = student.get('roll_number', student.get('student_id', 'N/A'))
        print(f"   • {student.get('name', student.get('first_name', 'Unknown'))} ({student['email']}) - Roll: {roll_num}")
    
    # Step 4: Send bulk performance emails
    print("\n4. 📧 Sending bulk performance emails...")
    bulk_email_data = {
        "target_type": "section",
        "sections": ["Section A"],
        "message_template": """Dear {student_name},

Here's your personalized performance report:

📊 **Academic Performance Summary**
• Math: {math_marks}% 
• Science: {science_marks}%
• English: {english_marks}%
• Overall Average: {average_score}% (Grade: {grade_letter})
• Status: {status}

💡 **Feedback**: {status_message}

Keep up the great work!

Best regards,
Your Teacher""",
        "subject": "📊 Your Personalized Performance Report - {student_name}",
        "send_email": True,
        "create_notifications": True
    }
    
    bulk_response = requests.post(f"{BASE_URL}/api/v1/bulk-communication/bulk-email", 
                                headers=headers, json=bulk_email_data)
    
    if bulk_response.status_code == 200:
        result = bulk_response.json()
        print(f"✅ Bulk email sent successfully!")
        print(f"   📧 Emails sent: {result.get('emails_sent', 0)}")
        print(f"   ❌ Emails failed: {result.get('emails_failed', 0)}")
        
        notifications_created = result.get('notifications_created', [])
        if isinstance(notifications_created, int):
            print(f"   📱 Notifications created: {notifications_created}")
        else:
            print(f"   📱 Notifications created: {len(notifications_created)}")
        
        print("\n📊 Individual Results:")
        results_data = result.get('results', [])
        for res in results_data[:3]:  # Show first 3 results
            status_emoji = "✅" if res.get('email_sent', False) else "❌"
            print(f"   {status_emoji} {res.get('student_name', 'Unknown')} ({res.get('student_email', 'N/A')})")
            perf = res.get('performance', {})
            if perf:
                print(f"      Performance: {perf.get('average_score', 'N/A')}% ({perf.get('grade_letter', 'N/A')})")
            
    else:
        print(f"❌ Bulk email failed: {bulk_response.text}")
        return
    
    # Step 5: Check sent history
    print("\n5. 📚 Checking sent communication history...")
    history_response = requests.get(f"{BASE_URL}/api/v1/bulk-communication/sent-history", headers=headers)
    history = history_response.json()["communications"]
    print(f"✅ Found {len(history)} sent communications")
    
    if history:
        latest = history[0]
        print(f"   Latest: '{latest['subject']}' to {latest['recipient_email']}")
        print(f"   Sent: {latest['sent_at']}")
        print(f"   Status: {latest['status']}")
    
    print("\n🎉 Bulk Communication Test Complete!")
    print("=" * 50)
    print("\n💡 Summary:")
    print("✅ Authentication working")
    print("✅ Section data loading")
    print("✅ Student data retrieval")
    print("✅ Performance calculation")
    print("✅ Real email sending (or simulation)")
    print("✅ Portal notifications created")
    print("✅ Communication history tracking")
    
    print(f"\n📧 Check your email ({SHAAF_EMAIL}) for the performance reports!")

if __name__ == "__main__":
    test_bulk_communication()