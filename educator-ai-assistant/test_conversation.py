#!/usr/bin/env python3

# Test the full conversation flow

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_conversation_flow():
    """Test the full conversation flow for parent meeting scheduling"""
    
    try:
        from app.api.ai_assistant import handle_ai_assistant_command, ConversationState
        from app.models.educator import Educator
        
        # Mock educator
        educator = type('MockEducator', (), {})()
        educator.id = 1
        educator.first_name = "Test"
        educator.last_name = "Teacher"
        
        print("=== Testing Full Conversation Flow ===\n")
        
        # Simulate the conversation
        test_conversation = [
            ("hey", "Should show greeting"),
            ("schedule meetings", "Should ask for student name"),
            ("alice anderson", "Should recognize as student name and continue"),
        ]
        
        state = ConversationState("test_user")
        
        for i, (command, expected) in enumerate(test_conversation):
            print(f"Step {i+1}: '{command}' - {expected}")
            
            try:
                response = handle_ai_assistant_command(
                    command=command,
                    language="en",
                    mode="assist", 
                    educator_id=1
                )
                
                print(f"Response: {response.response_text[:100]}...")
                print(f"Assistant State: {response.assistant_state}")
                print()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                print()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")

if __name__ == "__main__":
    test_conversation_flow()