#!/usr/bin/env python3
"""
Test the enhanced AI API via HTTP
"""

import asyncio
import aiohttp
import json

async def test_enhanced_ai_api():
    """Test the enhanced AI API via HTTP requests"""
    
    print("🌐 TESTING ENHANCED AI VIA HTTP API")
    print("=" * 50)
    
    # Login first to get a token
    async with aiohttp.ClientSession() as session:
        try:
            # Test the basic health endpoint
            async with session.get('http://localhost:8003/health') as response:
                if response.status == 200:
                    print("✅ Server is running and healthy")
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return
            
            # Test enhanced AI status endpoint
            async with session.get('http://localhost:8003/api/v1/gemini-assistant/status') as response:
                if response.status == 200:
                    status_data = await response.json()
                    print(f"✅ Enhanced AI Status: {status_data['status']}")
                    print(f"🤖 Assistant State: {status_data['assistant_state']}")
                    print(f"🎯 Autonomy Mode: {status_data['autonomy_mode']}")
                    print(f"🌍 Language: {status_data['language']}")
                else:
                    print(f"❌ Status check failed: {response.status}")
            
            # Test enhanced AI chat without authentication (should work for demo)
            test_messages = [
                "hey",
                "wassup", 
                "show me my students",
                "who are the top performers?"
            ]
            
            print(f"\n🎯 Testing {len(test_messages)} messages via API...\n")
            
            for i, message in enumerate(test_messages, 1):
                print(f"{i}. Testing: '{message}'")
                print("-" * 40)
                
                chat_data = {
                    "message": message,
                    "autonomy_mode": "assist",
                    "language": "en"
                }
                
                try:
                    async with session.post(
                        'http://localhost:8003/api/v1/gemini-assistant/enhanced-chat',
                        json=chat_data,
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Response: {result['response'][:100]}...")
                            print(f"🎯 State: {result['state']}")
                            print(f"📊 Actions: {len(result['actions'])}")
                            print(f"⚠️  Requires Approval: {result['requires_approval']}")
                        else:
                            error_text = await response.text()
                            print(f"❌ API Error {response.status}: {error_text}")
                
                except Exception as e:
                    print(f"❌ Request Error: {e}")
                
                print()
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_ai_api())