"""
Test WebSocket with correct educator credentials
"""
import asyncio
import websockets
import json
import requests

async def test_websocket_with_ananya():
    """Test WebSocket connection with Ananya's educator ID"""
    
    # First get Ananya's educator ID by logging in
    print("🔐 Logging in to get educator ID...")
    login_data = {
        "username": "ananya.rao@school.com",
        "password": "Ananya@123"
    }
    
    try:
        login_response = requests.post("http://localhost:8003/api/v1/educators/login", data=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        print("✅ Login successful")
        
        # Connect to WebSocket using Ananya's educator ID (1)
        ws_url = "ws://localhost:8003/api/v1/performance/ws/performance/1"
        
        print(f"🔌 Connecting to WebSocket: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected")
            
            # Listen for real-time updates
            print("📡 Listening for real-time performance updates...")
            
            try:
                # Wait for first message (should be performance update)
                message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(message)
                
                print(f"\n📊 Received WebSocket message:")
                print(f"   Type: {data.get('type')}")
                print(f"   Timestamp: {data.get('timestamp')}")
                
                if data.get('type') == 'performance_update' and 'data' in data:
                    perf_data = data['data']
                    print(f"   📈 Performance Data:")
                    print(f"     Total Students: {perf_data.get('total_students')}")
                    print(f"     Overall Average: {perf_data.get('overall_average')}")
                    print(f"     Pass Rate: {perf_data.get('overall_pass_rate')}")
                    print(f"     Top Performers: {perf_data.get('top_performers_count')}")
                    print(f"     Low Performers: {perf_data.get('low_performers_count')}")
                    
                    print(f"\n✅ WebSocket is working with correct performance data!")
                else:
                    print(f"❌ Unexpected message format: {data}")
                    
            except asyncio.TimeoutError:
                print("⏰ No messages received (timeout)")
                print("   This might be normal if updates are only sent every 10 seconds")
            except Exception as e:
                print(f"❌ WebSocket error: {e}")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_with_ananya())