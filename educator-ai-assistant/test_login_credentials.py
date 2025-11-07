"""
Test login credentials for shaafiya07@gmail.com
"""
import requests

def test_login_credentials():
    """Test different password combinations"""
    
    base_url = "http://localhost:8001"
    email = "shaafiya07@gmail.com"
    
    passwords_to_try = [
        "password123",
        "shaaf123", 
        "123456",
        "admin",
        "shaafiya",
        "password",
        "test123"
    ]
    
    print(f"🔐 Testing login credentials for: {email}")
    print("=" * 50)
    
    for password in passwords_to_try:
        print(f"\nTrying password: {password}")
        
        login_data = {
            "username": email,
            "password": password
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/educators/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Password '{password}' works!")
                token = response.json().get('access_token', 'No token')
                print(f"Token: {token[:20]}...")
                return password
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n❌ No valid password found for {email}")
    return None

if __name__ == "__main__":
    test_login_credentials()