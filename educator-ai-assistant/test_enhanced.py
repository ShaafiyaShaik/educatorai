#!/usr/bin/env python3

# Test the enhanced AI assistant capabilities

def test_enhanced_capabilities():
    """Test various enhanced AI assistant commands"""
    
    test_commands = [
        "hey",
        "hello", 
        "Schedule parent meeting for Alice Anderson tomorrow morning",
        "Send marks to Section A parents",
        "Generate attendance report for this week",
        "Show me dashboard overview",
        "Mark attendance for Section B",
        "Schedule staff meeting for Friday",
        "help",
        "create report",
        "student review for John Smith",
        "bulk communication"
    ]
    
    # Import detection functions
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from app.api.ai_assistant import detect_language, fuzzy_match_intent
        
        # Enhanced intents from the updated code
        intents = {
            'parent_meeting': ['parent', 'meeting', 'schedule', 'parents', 'discuss', 'talk', 'conference', 'appointment'],
            'staff_meeting': ['staff', 'teacher', 'department', 'colleague', 'faculty', 'team', 'meeting'],
            'student_review': ['student', 'review', 'consultation', 'counseling', 'guidance', 'session'],
            'schedule': ['schedule', 'book', 'arrange', 'plan', 'set up', 'organize', 'calendar', 'appointment'],
            'greeting': ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'start', 'namaste', 'namaskar'],
            'help': ['help', 'assist', 'support', 'what can you do', 'commands', 'guide'],
            'student_info': ['student', 'progress', 'grade', 'performance', 'attendance', 'marks', 'scores'],
            'bulk_communication': ['send', 'email', 'notify', 'message', 'inform', 'section', 'class', 'bulk', 'all'],
            'reports': ['report', 'summary', 'analysis', 'generate', 'export', 'download', 'statistics'],
            'document_management': ['document', 'file', 'form', 'certificate', 'letter', 'generate', 'create'],
            'dashboard': ['dashboard', 'overview', 'summary', 'today', 'pending', 'urgent', 'tasks'],
            'attendance': ['attendance', 'absent', 'present', 'roll', 'call', 'participation'],
            'marks_management': ['marks', 'grades', 'scores', 'results', 'assessment', 'evaluation'],
            'section_management': ['section', 'class', 'group', 'assign', 'manage', 'organize']
        }
        
        print("=== Enhanced AI Assistant Capability Test ===\n")
        
        for command in test_commands:
            print(f"Command: '{command}'")
            
            # Test language detection
            detected_language = detect_language(command)
            print(f"  Language: {detected_language}")
            
            # Test intent scoring
            intent_scores = {}
            for intent, keywords in intents.items():
                intent_scores[intent] = fuzzy_match_intent(command, keywords)
            
            # Get best intent
            best_intent = max(intent_scores, key=intent_scores.get)
            best_score = intent_scores[best_intent]
            
            print(f"  Best Intent: {best_intent} (score: {best_score:.2f})")
            
            # Show top 3 intents
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  Top Intents: {[(intent, f'{score:.2f}') for intent, score in sorted_intents]}")
            
            # Determine handler using the actual enhanced routing logic
            command_lower = command.lower()
            
            if best_intent == 'greeting' and best_score > 0.2:
                handler = "✅ GREETING response"
            elif best_intent == 'staff_meeting' or ('staff' in command_lower and 'meeting' in command_lower) or ('schedule' in command_lower and ('staff' in command_lower or 'department' in command_lower)):
                handler = "✅ STAFF_MEETING handler"
            elif best_intent == 'parent_meeting' or ('schedule' in command_lower and ('parent' in command_lower or 'meeting' in command_lower)) and not ('staff' in command_lower):
                handler = "✅ PARENT_MEETING handler" 
            elif best_intent == 'student_review' or ('student' in command_lower and ('review' in command_lower or 'consultation' in command_lower)):
                handler = "✅ STUDENT_REVIEW handler"
            elif best_intent == 'bulk_communication' or ('send' in command_lower and ('section' in command_lower or 'class' in command_lower or 'all' in command_lower or 'parents' in command_lower)) or ('send' in command_lower and ('marks' in command_lower or 'grades' in command_lower)):
                handler = "✅ BULK_COMMUNICATION handler"
            elif best_intent == 'reports' or ('report' in command_lower or 'generate' in command_lower):
                handler = "✅ REPORTS handler"
            elif best_intent == 'dashboard' or ('dashboard' in command_lower or 'overview' in command_lower or 'today' in command_lower):
                handler = "✅ DASHBOARD handler"
            elif best_intent == 'attendance' or 'attendance' in command_lower or ('mark' in command_lower and 'attendance' in command_lower):
                handler = "✅ ATTENDANCE handler"
            elif best_intent == 'marks_management' or (('marks' in command_lower or 'grades' in command_lower) and 'send' not in command_lower):
                handler = "✅ MARKS handler"
            elif best_intent == 'section_management' or ('section' in command_lower and ('manage' in command_lower or 'assign' in command_lower)):
                handler = "✅ SECTION_MANAGEMENT handler"
            elif best_intent == 'help' and best_score > 0.5:
                handler = "✅ HELP response"
            else:
                handler = "⚠️ DEFAULT response"
            
            print(f"  Handler: {handler}")
            print()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory.")

if __name__ == "__main__":
    test_enhanced_capabilities()