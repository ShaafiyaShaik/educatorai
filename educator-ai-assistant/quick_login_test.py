import requests

print("🧪 Testing login with corrected database configuration...")

login_data = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}

try:
    response = requests.post('http://localhost:8003/api/v1/educators/login', 
                           data=login_data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ SUCCESS! Login successful!")
        print(f"   Access Token: {token_data.get('access_token', 'No token')[:50]}...")
        print(f"   Token Type: {token_data.get('token_type', 'No type')}")
    else:
        print(f"❌ FAILED: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Connection Error: {e}")