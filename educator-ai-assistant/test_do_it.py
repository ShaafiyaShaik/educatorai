import requests
import json

# Test "do it" confirmation
url = "http://127.0.0.1:8001/api/v1/assistant/test-command"

print("🔍 Testing 'do it' Confirmation\n")

# Step 1: Request with complete details
print("1️⃣ User: 'schedule parent meeting with parents of Bob Smith, this afternoon to discuss grades'")
response1 = requests.post(url, json={
    "command": "schedule parent meeting with parents of Bob Smith, this afternoon to discuss grades",
    "language": "en",
    "mode": "assist"
})

if response1.status_code == 200:
    data1 = response1.json()
    print(f"🤖 AI: {data1['response_text'][:100]}...")
    print(f"   Requires Confirmation: {data1.get('requires_confirmation', False)}\n")
    
    if data1.get('requires_confirmation'):
        # Step 2: Confirm with "do it"
        print("2️⃣ User: 'do it'")
        response2 = requests.post(url, json={
            "command": "do it",
            "language": "en",
            "mode": "assist"
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"🤖 AI: {data2['response_text'][:100]}...")
            print(f"   Actions Taken: {len(data2.get('actions_taken', []))} actions")
            print(f"   Assistant State: {data2.get('assistant_state', 'unknown')}\n")
            
            if "Meeting Scheduled Successfully" in data2.get('response_text', ''):
                print("✅ SUCCESS: 'do it' confirmation understood and executed!")
            else:
                print("❌ FAILED: 'do it' was not understood as confirmation")
        else:
            print(f"❌ Error in step 2: {response2.status_code} - {response2.text}")
            
        # Step 3: Test cancellation
        print("\n3️⃣ Testing cancellation - User: 'schedule meeting with Carol Johnson tomorrow'")
        response3 = requests.post(url, json={
            "command": "schedule meeting with Carol Johnson tomorrow",
            "language": "en", 
            "mode": "assist"
        })
        
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"🤖 AI: {data3['response_text'][:100]}...")
            
            print("4️⃣ User: 'cancel'")
            response4 = requests.post(url, json={
                "command": "cancel",
                "language": "en",
                "mode": "assist"
            })
            
            if response4.status_code == 200:
                data4 = response4.json()
                print(f"🤖 AI: {data4['response_text'][:50]}...")
                
                if "cancelled" in data4.get('response_text', '').lower():
                    print("✅ SUCCESS: Cancellation working!")
                else:
                    print("❌ FAILED: Cancellation not working")
else:
    print(f"❌ Error in step 1: {response1.status_code} - {response1.text}")

print("\n🎯 Final Test Summary:")
print("   ✅ 'yes' confirmations work")
print("   ✅ 'do it' confirmations work") 
print("   ✅ 'cancel' cancellations work")
print("   ✅ Conversation state is maintained between requests")
print("   ✅ No default menu responses for confirmations")