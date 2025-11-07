#!/usr/bin/env python3
"""
Quick test of enhanced AI assistant API directly
"""

import sys
sys.path.append('.')

import asyncio
from app.agents.gemini_assistant import gemini_assistant
from app.core.database import get_db
from app.models.educator import Educator

async def test_enhanced_ai_directly():
    """Test the enhanced AI directly without server"""
    
    print("🤖 TESTING ENHANCED AI ASSISTANT DIRECTLY")
    print("=" * 50)
    
    # Get database and educator
    db = next(get_db())
    educator = db.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
    
    if not educator:
        print("❌ Test educator not found")
        return
    
    # Test commands that teachers commonly use
    test_commands = [
        "hey",
        "wassup", 
        "show me my students",
        "who are the top performers?",
        "help me find struggling students"
    ]
    
    print(f"🎯 Testing {len(test_commands)} commands directly...\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"{i}. Command: '{command}'")
        print("-" * 40)
        
        try:
            # Process command with enhanced AI
            result = await gemini_assistant.process_command(command, educator.id, db)
            
            print(f"✅ Response: {result['response']}")
            print(f"🎯 State: {result['state']}")
            print(f"📊 Actions: {len(result['actions'])} suggested")
            print(f"⚠️  Requires Approval: {result['requires_approval']}")
            
            if result['actions']:
                print("📋 Actions:")
                for j, action in enumerate(result['actions'], 1):
                    print(f"   {j}. {action.get('action', {}).get('description', 'Action')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    db.close()
    print("🎉 Direct AI Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_ai_directly())