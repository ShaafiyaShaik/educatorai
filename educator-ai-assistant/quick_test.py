import requests
import json

# Simple test of conversation state management
url = "http://127.0.0.1:8001/api/v1/assistant/test-command"

print("🔍 Testing Conversation State Management\n")

# Step 1: Request with complete details
print("1️⃣ User: 'schedule parent meeting with parents of Alice Anderson, tomorrow morning to discuss her attendance'")
response1 = requests.post(url, json={
    "command": "schedule parent meeting with parents of Alice Anderson, tomorrow morning to discuss her attendance",
    "language": "en",
    "mode": "assist"
})

if response1.status_code == 200:
    data1 = response1.json()
    print(f"🤖 AI: {data1['response_text'][:100]}...")
    print(f"   Requires Confirmation: {data1.get('requires_confirmation', False)}")
    print(f"   Assistant State: {data1.get('assistant_state', 'unknown')}\n")
    
    if data1.get('requires_confirmation'):
        # Step 2: Confirm with "yes"
        print("2️⃣ User: 'yes'")
        response2 = requests.post(url, json={
            "command": "yes",
            "language": "en",
            "mode": "assist"
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"🤖 AI: {data2['response_text'][:100]}...")
            print(f"   Actions Taken: {len(data2.get('actions_taken', []))} actions")
            print(f"   Assistant State: {data2.get('assistant_state', 'unknown')}\n")
            
            if "Meeting Scheduled Successfully" in data2.get('response_text', ''):
                print("✅ SUCCESS: Conversation state working! 'yes' confirmation understood")
            else:
                print("❌ FAILED: 'yes' was not understood as confirmation")
        else:
            print(f"❌ Error in step 2: {response2.status_code} - {response2.text}")
    else:
        print("ℹ️ No confirmation required for this request")
else:
    print(f"❌ Error in step 1: {response1.status_code} - {response1.text}")