#!/usr/bin/env python3
"""
Test script to verify conversation state management works correctly
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_conversation_flow():
    """Test the conversation state management"""
    
    print("🧪 Testing Enhanced Conversation State Management\n")
    
    # First, create a test user session
    educator_id = 1  # Assuming user ID 1 exists
    
    # Test 1: Start parent meeting conversation
    print("📅 Test 1: Starting parent meeting conversation")
    response1 = requests.post(f"{BASE_URL}/api/v1/assistant/test-command", json={
        "command": "schedule parent meeting",
        "language": "en",
        "mode": "assist"
    })
    
    result1 = response1.json()
    print(f"Raw response 1: {result1}")
    print(f"Response 1: {result1.get('response_text', 'No response_text found')}")
    print(f"State: {result1.get('assistant_state', 'N/A')}\n")
    
    # Test 2: Provide student name (should maintain context)
    print("👤 Test 2: Providing student name")
    response2 = requests.post(f"{BASE_URL}/api/v1/assistant/test-command", json={
        "command": "Alice Anderson",
        "language": "en",
        "mode": "assist"
    })
    
    result2 = response2.json()
    print(f"Raw response 2: {result2}")
    print(f"Response 2: {result2.get('response_text', 'No response_text found')}")
    print(f"State: {result2.get('assistant_state', 'N/A')}\n")
    
    # Test 3: Provide timing (should maintain context and ask for confirmation)
    print("⏰ Test 3: Providing timing")
    response3 = requests.post(f"{BASE_URL}/api/v1/assistant/test-command", json={
        "command": "tomorrow morning",
        "language": "en",
        "mode": "assist"
    })
    
    result3 = response3.json()
    print(f"Response 3: {result3.get('response_text', 'No response_text found')}")
    print(f"State: {result3.get('assistant_state', 'N/A')}")
    print(f"Requires Confirmation: {result3.get('requires_confirmation', False)}\n")
    
    # Test 4: Confirm the meeting
    print("✅ Test 4: Confirming the meeting")
    response4 = requests.post(f"{BASE_URL}/api/v1/assistant/test-command", json={
        "command": "yes, book it",
        "language": "en",
        "mode": "assist"
    })
    
    result4 = response4.json()
    print(f"Response 4: {result4.get('response_text', 'No response_text found')}")
    print(f"State: {result4.get('assistant_state', 'N/A')}\n")
    
    print("🎉 Conversation state test completed!")

if __name__ == "__main__":
    try:
        test_conversation_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on http://127.0.0.1:8001")
    except Exception as e:
        print(f"❌ Error during testing: {e}")