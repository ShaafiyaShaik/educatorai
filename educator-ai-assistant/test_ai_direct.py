#!/usr/bin/env python3
"""
Complete conversation flow test directly
"""

import sys
sys.path.append('.')

try:
    from app.api.ai_assistant import handle_ai_assistant_command
    print("✅ Import successful")
    
    # Test 1: Start staff meeting request
    print("\n📅 Test 1: Starting staff meeting conversation")
    response1 = handle_ai_assistant_command("schedule staff meeting", "en", "assist", 1)
    print(f"Response 1: {response1.response_text}")
    print(f"State: {response1.assistant_state}\n")
    
    # Test 2: Provide timing
    print("⏰ Test 2: Providing timing")
    response2 = handle_ai_assistant_command("tomorrow morning", "en", "assist", 1)
    print(f"Response 2: {response2.response_text}")
    print(f"State: {response2.assistant_state}")
    print(f"Requires Confirmation: {response2.requires_confirmation}\n")
    
    # Test 3: Confirm the meeting
    print("✅ Test 3: Confirming the meeting")
    print("DEBUG: Checking confirmation detection...")
    from app.api.ai_assistant import is_confirmation
    print(f"Is 'yes, book it' a confirmation? {is_confirmation('yes, book it')}")
    
    response3 = handle_ai_assistant_command("yes, book it", "en", "assist", 1)
    print(f"Response 3: {response3.response_text}")
    print(f"State: {response3.assistant_state}\n")
    
    print("🎉 Conversation flow test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()