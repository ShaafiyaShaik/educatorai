#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ai_assistant import handle_ai_assistant_command
from app.models.educator import Educator

def test_greeting_response():
    """Test the greeting response directly"""
    
    # Create a mock educator
    educator = Educator()
    educator.id = 1
    educator.first_name = "Test"
    educator.last_name = "Teacher"
    
    # Test cases
    test_cases = [
        "hey",
        "hi", 
        "hello",
        "good morning"
    ]
    
    for command in test_cases:
        print(f"\n=== Testing: '{command}' ===")
        try:
            response = handle_ai_assistant_command(
                command=command,
                language="en",  # This should be ignored due to auto-detection
                mode="assist",
                educator_id=1,
                state=None
            )
            
            print(f"Response Text: {response.response_text[:100]}...")
            print(f"Language: {response.language}")
            print(f"Assistant State: {response.assistant_state}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_greeting_response()