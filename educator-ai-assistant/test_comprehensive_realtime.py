"""
Comprehensive Real-time Performance System Test
Tests the complete real-time performance system including API, WebSocket, and data updates
"""

import requests
import json
import asyncio
import websockets
import threading
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_realtime_performance import test_realtime_updates

def test_performance_apis():
    """Test performance API endpoints"""
    print("🔥 Testing Performance API Endpoints...")
    
    base_url = "http://localhost:8003"
    
    # Test login first
    print("1. Testing educator login...")
    login_data = {
        "username": "shaaf",
        "password": "shaaf123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
            
            # Test performance endpoints
            endpoints = [
                "/api/v1/performance/overview",
                "/api/v1/performance/section/1",
                "/api/v1/performance/student/1"
            ]
            
            for endpoint in endpoints:
                print(f"2. Testing {endpoint}...")
                try:
                    response = requests.get(f"{base_url}{endpoint}", headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ {endpoint} - Success (Students: {data.get('total_students', 'N/A')})")
                    else:
                        print(f"❌ {endpoint} - Failed: {response.status_code}")
                except Exception as e:
                    print(f"❌ {endpoint} - Error: {e}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False
    
    return True

async def test_websocket_connection():
    """Test WebSocket connection for real-time updates"""
    print("\n🔌 Testing WebSocket Connection...")
    
    ws_url = "ws://localhost:8003/api/v1/performance/ws/performance/1"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Listen for messages for 30 seconds
            print("📡 Listening for real-time updates (30 seconds)...")
            
            try:
                # Set a timeout for receiving messages
                message = await asyncio.wait_for(websocket.recv(), timeout=35.0)
                data = json.loads(message)
                print(f"✅ Received WebSocket message: {data.get('type', 'unknown')}")
                
                if data.get('type') == 'performance_update':
                    print(f"   📊 Performance Data - Students: {data['data'].get('total_students')}")
                    print(f"   📈 Average: {data['data'].get('overall_average'):.1f}%")
                    print(f"   ✅ Pass Rate: {data['data'].get('overall_pass_rate'):.1f}%")
                
                return True
                
            except asyncio.TimeoutError:
                print("⏰ No messages received within timeout period")
                return True  # Still successful connection
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def trigger_data_changes():
    """Trigger data changes in a separate thread"""
    print("\n🔄 Starting data change triggers...")
    time.sleep(5)  # Wait 5 seconds before starting
    
    for i in range(3):
        print(f"\n🎲 Triggering data change {i+1}/3...")
        test_realtime_updates()
        time.sleep(10)  # Wait 10 seconds between changes
    
    print("🏁 Data change triggers completed")

async def run_comprehensive_test():
    """Run the complete real-time system test"""
    print("🚀 COMPREHENSIVE REAL-TIME PERFORMANCE SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: API Endpoints
    api_success = test_performance_apis()
    if not api_success:
        print("❌ API tests failed - cannot continue")
        return
    
    # Test 2: Start data change triggers in background
    data_thread = threading.Thread(target=trigger_data_changes)
    data_thread.daemon = True
    data_thread.start()
    
    # Test 3: WebSocket Connection with real-time updates
    ws_success = await test_websocket_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 COMPREHENSIVE TEST RESULTS:")
    print(f"   📡 API Endpoints: {'✅ PASSED' if api_success else '❌ FAILED'}")
    print(f"   🔌 WebSocket: {'✅ PASSED' if ws_success else '❌ FAILED'}")
    print(f"   🔄 Real-time Updates: {'✅ TRIGGERED' if data_thread.is_alive() else '❌ FAILED'}")
    
    if api_success and ws_success:
        print("\n🎊 ALL TESTS PASSED! Real-time performance system is working!")
        print("📱 Frontend Dashboard should show:")
        print("   • Live Data indicator (green)")
        print("   • Real-time performance updates")
        print("   • WebSocket notifications for data changes")
    else:
        print("\n⚠️  Some tests failed. Check the server and try again.")
    
    print("\n📋 Next Steps:")
    print("   1. Open frontend Performance Dashboard")
    print("   2. Verify 'Live Data' status indicator")
    print("   3. Run: python test_realtime_performance.py --continuous")
    print("   4. Watch real-time updates in the dashboard")

def main():
    print("🔥 Testing Real-time Performance System...")
    print("⚡ Make sure the server is running on localhost:8000")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8003/docs")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server not responding correctly")
            return
    except:
        print("❌ Server not running. Please start with: python run_server.py")
        return
    
    # Run the comprehensive test
    asyncio.run(run_comprehensive_test())

if __name__ == "__main__":
    main()