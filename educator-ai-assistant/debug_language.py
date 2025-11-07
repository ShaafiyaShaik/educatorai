#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ai_assistant import handle_ai_assistant_command, detect_language, fuzzy_match_intent

def test_language_detection():
    print("=== Testing Language Detection ===")
    
    test_cases = [
        "hey",
        "hi", 
        "hello",
        "నమస్కారం",
        "schedule meeting",
        "help"
    ]
    
    for command in test_cases:
        detected = detect_language(command)
        print(f"'{command}' -> {detected}")
    
    print("\n=== Testing Intent Detection ===")
    
    greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'start', 'namaste', 'namaskar']
    
    for command in test_cases:
        score = fuzzy_match_intent(command, greeting_keywords)
        print(f"'{command}' -> greeting score: {score}")

if __name__ == "__main__":
    test_language_detection()