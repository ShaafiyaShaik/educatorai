#!/usr/bin/env python3

# Test the improved name extraction and conversation flow

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_name_extraction():
    """Test the improved name extraction"""
    
    try:
        from app.api.ai_assistant import extract_student_name_flexible, extract_meeting_details
        
        test_cases = [
            "alice",
            "alice anderson", 
            "Alice",
            "Alice Anderson",
            "john smith",
            "John Smith",
            "Schedule parent meeting for Alice Anderson tomorrow morning",
            "schedule meetings",  # Should not extract a name
            "hello",  # Should not extract a name
        ]
        
        print("=== Testing Flexible Name Extraction ===\n")
        
        for command in test_cases:
            name = extract_student_name_flexible(command)
            print(f"'{command}' -> '{name}'")
        
        print("\n=== Testing Meeting Details Extraction ===\n")
        
        for command in test_cases:
            details = extract_meeting_details(command)
            student_name = details.get('student_name', 'None')
            print(f"'{command}' -> student_name: '{student_name}'")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")

if __name__ == "__main__":
    test_name_extraction()