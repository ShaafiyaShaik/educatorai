#!/usr/bin/env python3
"""
Test script for Enhanced Intelligent Intent Recognition
"""

import sys
sys.path.append('.')

import asyncio
from app.agents.gemini_assistant import gemini_assistant
from app.core.database import get_db
from app.models.educator import Educator

async def test_intent_recognition():
    """Test the enhanced intent recognition with various commands"""
    
    print("🧠 TESTING ENHANCED INTELLIGENT INTENT RECOGNITION")
    print("=" * 60)
    
    # Get database and educator
    db = next(get_db())
    educator = db.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
    
    if not educator:
        print("❌ Test educator 'ananya.rao@school.com' not found")
        return
    
    # Test commands that should be understood naturally
    test_commands = [
        # English commands
        "Show me my students",
        "Get the top 5 performing students in Section A", 
        "List students who are failing",
        "Who missed more than 3 classes this week?",
        "Send appreciation email to top students",
        "Schedule a meeting with parent of student S101",
        "Generate performance report for Section B",
        "How is Section C doing in Math?",
        "Show me grade summary",
        "Which students need help in Science?",
        
        # Telugu commands
        "విద్యార్థుల జాబితా చూపించు",
        "గ్రేడ్స్ చూపించు", 
        "రిపోర్ట్ తయారు చేయి",
        "ఇమెయిల్ పంపించు",
        
        # Casual/Natural commands
        "hey, can you show me who's doing well?",
        "I need to check attendance issues",
        "help me find struggling students",
        "what's my schedule today?",
    ]
    
    print(f"🎯 Testing {len(test_commands)} different commands...\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"{i:2d}. Testing: '{command}'")
        print("-" * 50)
        
        try:
            # Test intent analysis
            intent = await gemini_assistant.analyze_intent(command, educator.id)
            
            print(f"   ✅ Intent: {intent['intent']}")
            print(f"   🎯 Confidence: {intent['confidence']:.1f}")
            print(f"   ⚡ Action Type: {intent['action_type']}")
            print(f"   📝 Response: {intent.get('natural_response', 'N/A')}")
            
            if intent['entities']:
                print(f"   🔍 Entities: {intent['entities']}")
            
            if intent['requires_data']:
                print(f"   📊 Data Needed: {', '.join(intent['requires_data'])}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    db.close()
    
    print("🎉 Intent Recognition Test Complete!")
    print("\n💡 Next Step: Test full command processing with real data...")

async def test_full_processing():
    """Test full command processing including data gathering"""
    
    print("\n🚀 TESTING FULL COMMAND PROCESSING")
    print("=" * 50)
    
    db = next(get_db())
    educator = db.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
    
    if not educator:
        print("❌ Test educator not found")
        return
    
    # Test one complete flow
    test_command = "Show me the top 5 students in my sections"
    print(f"🎯 Processing: '{test_command}'\n")
    
    try:
        result = await gemini_assistant.process_command(test_command, educator.id, db)
        
        print("✅ Full Processing Result:")
        print(f"   Response: {result['response']}")
        print(f"   Actions: {len(result['actions'])} actions suggested")
        print(f"   State: {result['state']}")
        print(f"   Requires Approval: {result['requires_approval']}")
        
        if result['actions']:
            print(f"\n📋 Suggested Actions:")
            for i, action in enumerate(result['actions'], 1):
                print(f"   {i}. {action.get('action', {}).get('description', 'Action')}")
                
    except Exception as e:
        print(f"❌ Full processing error: {e}")
    
    db.close()

if __name__ == "__main__":
    print("🤖 EduAssist AI - Intelligent Intent Recognition Test")
    print("📅 Testing Date:", "October 29, 2025")
    print()
    
    asyncio.run(test_intent_recognition())
    asyncio.run(test_full_processing())