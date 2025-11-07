#!/usr/bin/env python3
"""
Test the running server with Gemini AI assistant
"""

import requests
import json

def test_server_running():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:8003/health")
        print(f"✅ Server is running: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return False

def test_login():
    """Test login functionality"""
    try:
        login_data = {
            "email": "shaaf@gmail.com", 
            "password": "password123"
        }
        response = requests.post("http://localhost:8003/api/v1/educators/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Login successful: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_gemini_assistant(token):
    """Test Gemini AI assistant"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        chat_data = {
            "message": "Show me student performance analytics for Computer Science A section",
            "autonomy_mode": "assist",
            "language": "en"
        }
        
        response = requests.post(
            "http://localhost:8003/api/v1/gemini-assistant/enhanced-chat", 
            json=chat_data, 
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Gemini Assistant Response:")
            print(f"   📝 Response: {result['response'][:100]}...")
            print(f"   🎯 Actions: {len(result['actions'])} actions suggested")
            print(f"   🤖 State: {result['state']}")
            print(f"   🌍 Language: {result['language']}")
            return True
        else:
            print(f"❌ Gemini Assistant failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini Assistant error: {e}")
        return False

def test_telugu_support(token):
    """Test Telugu language support"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        chat_data = {
            "message": "విద్యార్థుల గ్రేడ్స్ చూపించు",  # Telugu: Show student grades
            "autonomy_mode": "assist",
            "language": "te"
        }
        
        response = requests.post(
            "http://localhost:8003/api/v1/gemini-assistant/enhanced-chat", 
            json=chat_data, 
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Telugu Support Working:")
            print(f"   📝 Telugu Input Processed Successfully")
            print(f"   🎯 Actions: {len(result['actions'])} actions suggested")
            return True
        else:
            print(f"❌ Telugu support failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telugu support error: {e}")
        return False

def test_performance_data(token):
    """Test performance data endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8003/api/v1/performance/overview", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Performance Data Available:")
            print(f"   👥 Total Students: {data.get('total_students', 0)}")
            print(f"   📊 Overall Average: {data.get('overall_average', 0):.1f}%")
            print(f"   📈 Pass Rate: {data.get('overall_pass_rate', 0):.1f}%")
            return True
        else:
            print(f"❌ Performance data failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Performance data error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing EduAssist AI - Live Server Demo")
    print("=" * 50)
    
    # Test 1: Server running
    if not test_server_running():
        print("❌ Server is not running. Please start the server first.")
        return False
    
    # Test 2: Login
    token = test_login()
    if not token:
        print("❌ Login failed. Cannot proceed with other tests.")
        return False
    
    # Test 3: Gemini Assistant
    gemini_working = test_gemini_assistant(token)
    
    # Test 4: Telugu Support
    telugu_working = test_telugu_support(token)
    
    # Test 5: Performance Data
    performance_working = test_performance_data(token)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 DEMO READINESS STATUS")
    print("=" * 50)
    
    if all([gemini_working, telugu_working, performance_working]):
        print("✅ ALL SYSTEMS GO! Ready for presentation!")
        print("\n🎬 Demo Features Working:")
        print("   🤖 Gemini AI Assistant - READY")
        print("   🌍 Multilingual Support (Telugu) - READY") 
        print("   📊 Performance Analytics - READY")
        print("   🔐 Authentication System - READY")
        print("\n🚀 Your EduAssist AI is presentation-ready!")
        print("\n📋 Demo URLs:")
        print("   🖥️ API Server: http://localhost:8003")
        print("   📚 API Docs: http://localhost:8003/docs")
        print("   🔑 Login: shaaf@gmail.com / password123")
        return True
    else:
        print("⚠️ Some features need attention:")
        print(f"   Gemini AI: {'✅' if gemini_working else '❌'}")
        print(f"   Telugu Support: {'✅' if telugu_working else '❌'}")
        print(f"   Performance Data: {'✅' if performance_working else '❌'}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)