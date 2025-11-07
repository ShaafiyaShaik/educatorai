#!/usr/bin/env python3
"""
Debug calendar API response to understand timezone issues
"""

import requests
import json
from datetime import datetime

def test_calendar_api():
    print("🗓️ DEBUGGING CALENDAR API")
    print("=" * 50)
    
    try:
        # Login first
        login_data = {
            'username': 'shaaf@gmail.com',
            'password': 'password123'
        }
        
        print("1. Logging in...")
        response = requests.post('http://localhost:8001/api/v1/educators/login', data=login_data)
        
        if response.status_code == 200:
            token = response.json()['access_token']
            print(f"   ✅ Login successful")
            
            # Test calendar endpoint
            print("2. Calling calendar API...")
            headers = {'Authorization': f'Bearer {token}'}
            calendar_response = requests.get(
                'http://localhost:8001/api/v1/scheduling/calendar?start_date=2025-10-01&end_date=2025-10-31',
                headers=headers
            )
            
            print(f"   📊 Status Code: {calendar_response.status_code}")
            
            if calendar_response.status_code == 200:
                data = calendar_response.json()
                print(f"   ✅ SUCCESS! Calendar Response:")
                print(json.dumps(data, indent=2))
                
                if 'events' in data and len(data['events']) > 0:
                    print(f"\n📋 Events Analysis:")
                    for i, event in enumerate(data['events'], 1):
                        print(f"\n   Event {i}:")
                        print(f"     Title: {event.get('title', 'N/A')}")
                        print(f"     Start: {event.get('start', 'N/A')}")
                        print(f"     Start DateTime: {event.get('start_datetime', 'N/A')}")
                        print(f"     Local Date: {event.get('local_date', 'N/A')}")
                        
                        # Parse the start datetime to see what date it represents
                        start_str = event.get('start', '')
                        if start_str:
                            try:
                                # Parse as datetime and extract date
                                dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                                local_date = dt.date()
                                print(f"     Parsed Local Date: {local_date}")
                                print(f"     Full DateTime: {dt}")
                            except Exception as e:
                                print(f"     Parse Error: {e}")
                
            else:
                print(f"   ❌ Calendar API Error: {calendar_response.status_code}")
                print(f"      Response: {calendar_response.text}")
                
        else:
            print(f"   ❌ Login Error: {response.status_code}")
            print(f"      Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_calendar_api()