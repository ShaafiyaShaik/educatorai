#!/usr/bin/env python3
"""
Test the notifications API to see what data is returned
"""
import requests
import json

def test_notifications_api():
    try:
        # First login to get token
        login_data = {
            "email": "rahul.s101@school.com",
            "password": "student123"
        }
        
        login_response = requests.post("http://localhost:8003/api/v1/student-auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get notifications
        notifications_response = requests.get("http://localhost:8003/api/v1/student-dashboard/notifications", headers=headers)
        
        if notifications_response.status_code == 200:
            notifications = notifications_response.json()
            print(f"Got {len(notifications)} notifications")
            
            # Show the first few notifications with their structure
            for i, notif in enumerate(notifications[:3]):
                print(f"\nNotification {i+1}:")
                print(f"  ID: {notif.get('id')}")
                print(f"  Title: {notif.get('title')}")
                print(f"  Message Type: {notif.get('message_type')}")
                print(f"  Has report_data: {bool(notif.get('report_data'))}")
                if notif.get('report_data'):
                    print(f"  Report Data: {json.dumps(notif.get('report_data'), indent=4)}")
                print("  ---")
        else:
            print(f"API call failed: {notifications_response.status_code}")
            print(f"Response: {notifications_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_notifications_api()