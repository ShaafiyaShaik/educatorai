#!/usr/bin/env python3

# Simple test of just the core logic without database models

def detect_language(command: str) -> str:
    """Detect if the command should be responded to in Telugu or English"""
    import re
    
    # Check for Telugu script (Devanagari-like scripts)
    telugu_script_pattern = r'[\u0C00-\u0C7F]'
    if re.search(telugu_script_pattern, command):
        return "te"
    
    # Check for Telugu words written in English
    telugu_words = ['namaste', 'namaskar', 'namaskaram', 'dhanyawad', 'dhanyavadalu']
    command_lower = command.lower()
    for word in telugu_words:
        if word in command_lower:
            return "te"
    
    # Default to English
    return "en"

def fuzzy_match_intent(command: str, intent_keywords) -> float:
    """Calculate fuzzy match score for intent detection"""
    command_lower = command.lower().strip()
    score = 0
    matched_keywords = 0
    
    for keyword in intent_keywords:
        if keyword in command_lower:
            # Exact match gets higher score
            score += 1.0
            matched_keywords += 1
        else:
            # Check for partial matches
            for word in command_lower.split():
                if keyword in word or word in keyword:
                    score += 0.5
                    matched_keywords += 1
                    break
    
    # For short commands, if any keyword matches, give a high score
    if len(command_lower.split()) <= 2 and matched_keywords > 0:
        return min(score, 1.0)
    
    # For longer commands, use normalized score
    return min(score / len(intent_keywords), 1.0)

def test_logic():
    """Test the core logic"""
    
    intents = {
        'parent_meeting': ['parent', 'meeting', 'schedule', 'parents', 'discuss', 'talk', 'conference'],
        'schedule': ['schedule', 'book', 'arrange', 'plan', 'set up', 'organize'],
        'greeting': ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'start', 'namaste', 'namaskar'],
        'help': ['help', 'assist', 'support', 'what can you do', 'commands'],
        'student_info': ['student', 'progress', 'grade', 'performance', 'attendance']
    }
    
    test_cases = ["hey", "hi", "hello", "schedule", "help"]
    
    for command in test_cases:
        print(f"\n=== Testing: '{command}' ===")
        
        # Test language detection
        detected_language = detect_language(command)
        print(f"Detected Language: {detected_language}")
        
        # Test intent scoring
        intent_scores = {}
        for intent, keywords in intents.items():
            intent_scores[intent] = fuzzy_match_intent(command, keywords)
        
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        
        print(f"Intent Scores: {intent_scores}")
        print(f"Best Intent: {best_intent} (score: {best_score})")
        
        # Test greeting detection
        if best_intent == 'greeting' and best_score > 0.2:
            print("✅ Would trigger GREETING response")
            response_text = "👋 **Hello! Ready to help with your teaching tasks.**" if detected_language == "en" else "👋 **నమస్కారం! మీ బోధనా పనులతో సహాయం చేయడానికి సిద్ధంగా ఉన్నాను.**"
            print(f"Response: {response_text[:50]}...")
        else:
            print("❌ Would fall through to default response")

if __name__ == "__main__":
    test_logic()