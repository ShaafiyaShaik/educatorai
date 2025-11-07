import requests
import json

# Test login with available users
BASE_URL = "http://localhost:8001"

# Test users from the database
test_users = [
    {"email": "shaafiya07@gmail.com", "password": "password123"},  # Common default
    {"email": "shaaf123@gmail.com", "password": "password123"},
    {"email": "shaaf@gmail.com", "password": "password123"},
    {"email": "john.doe@university.edu", "password": "password123"},
    {"email": "teacher1@example.com", "password": "password123"},
]

def test_login(email, password):
    """Test login with given credentials"""
    print(f"\n🔐 Testing login for: {email}")
    
    try:
        # Prepare login data (OAuth2PasswordRequestForm format)
        login_data = {
            "username": email,  # OAuth2 uses 'username' field for email
            "password": password
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/educators/login",
            data=login_data,  # Use 'data' for form data, not 'json'
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ LOGIN SUCCESS!")
            print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
            return data.get('access_token')
        else:
            print("❌ Login failed")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def test_authenticated_endpoint(token):
    """Test an authenticated endpoint"""
    if not token:
        return
        
    print(f"\n🔍 Testing authenticated endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/educators/me", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Authenticated request SUCCESS!")
            print(f"User: {data.get('first_name')} {data.get('last_name')} ({data.get('email')})")
        else:
            print("❌ Authenticated request failed")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Login System...")
    print("="*50)
    
    working_token = None
    
    for user in test_users:
        token = test_login(user["email"], user["password"])
        if token:
            working_token = token
            break
    
    if working_token:
        test_authenticated_endpoint(working_token)
        print(f"\n✅ SOLUTION: Use email '{user['email']}' with password '{user['password']}'")
    else:
        print(f"\n❌ None of the test passwords worked.")
        print("💡 You may need to reset a user's password or create a new test user.")
        
    print("="*50)