#!/usr/bin/env python3
"""
Test the tasks API endpoint directly
"""

import requests
import json

def test_tasks_api():
    print("🧪 TESTING TASKS API")
    print("=" * 40)
    
    try:
        # Login first
        login_data = {
            'username': 'shaaf@gmail.com',
            'password': 'password123'
        }
        
        print("1. Logging in...")
        response = requests.post('http://127.0.0.1:8001/api/v1/educators/login', data=login_data)
        
        if response.status_code == 200:
            token = response.json()['access_token']
            print(f"   ✅ Login successful")
            
            # Test tasks endpoint
            print("2. Calling /api/v1/scheduling/tasks...")
            headers = {'Authorization': f'Bearer {token}'}
            tasks_response = requests.get('http://127.0.0.1:8001/api/v1/scheduling/tasks', headers=headers)
            
            print(f"   📊 Status Code: {tasks_response.status_code}")
            
            if tasks_response.status_code == 200:
                data = tasks_response.json()
                print(f"   ✅ SUCCESS! API Response:")
                print(json.dumps(data, indent=2))
                
                if 'tasks' in data and len(data['tasks']) > 0:
                    task = data['tasks'][0]
                    print(f"\n📋 First Task Details:")
                    print(f"   Title: {task.get('title', 'N/A')}")
                    print(f"   Description: {task.get('description', 'N/A')}")
                    print(f"   Scheduled Date: {task.get('scheduled_date', 'N/A')}")
                    print(f"   Scheduled Time: {task.get('scheduled_time', 'N/A')}")
                    print(f"   Duration: {task.get('duration_minutes', 'N/A')} minutes")
                    print(f"   Location: {task.get('location', 'N/A')}")
                    print(f"   Status: {task.get('status', 'N/A')}")
                    print(f"   Task Type: {task.get('task_type', 'N/A')}")
                    print(f"   Participants: {task.get('participants', 'N/A')}")
                    print(f"   Preparation Notes: {task.get('preparation_notes', 'N/A')}")
                    print(f"   Materials Needed: {task.get('materials_needed', 'N/A')}")
                
            else:
                print(f"   ❌ API Error: {tasks_response.status_code}")
                print(f"      Response: {tasks_response.text}")
                
        else:
            print(f"   ❌ Login Error: {response.status_code}")
            print(f"      Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_tasks_api()