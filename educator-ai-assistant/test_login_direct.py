import requests
import json

def test_login_direct():
    """Test login endpoint directly"""
    
    BASE_URL = "http://localhost:8001"
    
    # Test login with the credentials
    login_data = {
        "username": "test@test.com",  # OAuth2 uses 'username' field for email
        "password": "test123"
    }
    
    print("🔐 Testing login...")
    print(f"📧 Email: {login_data['username']}")
    print(f"🔑 Password: {login_data['password']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/educators/login",
            data=login_data,  # Use 'data' for form data
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ LOGIN SUCCESS!")
            print(f"🎟️ Token: {data.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print("❌ LOGIN FAILED")
            print(f"Error Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"Error Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                pass
            
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_server_status():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:8001/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
    except:
        print("❌ Server not responding")
        return False

if __name__ == "__main__":
    print("🚀 Testing Login System...")
    print("="*40)
    
    # Check server first
    if not check_server_status():
        print("\n💡 Start the server first:")
        print("python run_server.py")
        exit(1)
    
    # Test login
    success = test_login_direct()
    
    if not success:
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if server is running on port 8001")
        print("2. Check database connection")
        print("3. Verify user exists with correct password")
    
    print("="*40)