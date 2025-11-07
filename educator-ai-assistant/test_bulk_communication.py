#!/usr/bin/env python3
"""Test script to verify bulk communication improvements"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ai_assistant import handle_ai_assistant_command

def test_bulk_communication_improvements():
    """Test the improved bulk communication flow"""
    
    print("🧪 Testing Bulk Communication Improvements")
    print("=" * 50)
    
    # Test case 1: "send email"
    print("\n🧪 Test 1: 'send email'")
    print("-" * 30)
    response1 = handle_ai_assistant_command("send email", educator_id=1)
    print(f"Response: {response1.response_text[:100]}...")
    print(f"Assistant State: {response1.assistant_state}")
    
    # Test case 2: "section B"
    print("\n🧪 Test 2: 'section B'")
    print("-" * 30)
    response2 = handle_ai_assistant_command("section B", educator_id=1)
    print(f"Response: {response2.response_text[:100]}...")
    print(f"Assistant State: {response2.assistant_state}")
    
    # Test case 3: "section B students"
    print("\n🧪 Test 3: 'section B students'")
    print("-" * 30)
    response3 = handle_ai_assistant_command("section B students", educator_id=1)
    print(f"Response: {response3.response_text[:100]}...")
    print(f"Assistant State: {response3.assistant_state}")
    
    # Test case 4: "all students"
    print("\n🧪 Test 4: 'all students'")
    print("-" * 30)
    response4 = handle_ai_assistant_command("all students", educator_id=1)
    print(f"Response: {response4.response_text[:100]}...")
    print(f"Assistant State: {response4.assistant_state}")
    
    # Test case 5: Full conversation flow simulation
    print("\n🧪 Test 5: Full Conversation Flow")
    print("-" * 30)
    
    # Step 1: Start with "send email"
    response = handle_ai_assistant_command("send email", educator_id=1)
    print(f"Step 1 - 'send email': {response.response_text[:80]}...")
    
    # Step 2: Follow up with "section B"
    response = handle_ai_assistant_command("section B", educator_id=1)
    print(f"Step 2 - 'section B': {response.response_text[:80]}...")
    
    # Step 3: Follow up with "marks"
    response = handle_ai_assistant_command("marks", educator_id=1)
    print(f"Step 3 - 'marks': {response.response_text[:80]}...")
    
    # Step 4: Confirm with "yes"
    response = handle_ai_assistant_command("yes", educator_id=1)
    print(f"Step 4 - 'yes': {response.response_text[:80]}...")
    
    print("\n✅ Bulk Communication Testing Complete!")

if __name__ == "__main__":
    test_bulk_communication_improvements()