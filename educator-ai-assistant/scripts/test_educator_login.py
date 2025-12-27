"""
Test educator login with the API
"""
import requests
import json

BASE_URL = "http://localhost:8003"

print("=" * 70)
print("TESTING EDUCATOR LOGIN")
print("=" * 70)

test_credentials = [
    {"email": "ananya.rao@school.com", "password": "Ananya@123"},
    {"email": "jennifer.educator@school.com", "password": "Jennifer@123"},
    {"email": "nicole.educator@school.com", "password": "Nicole@123"},
    {"email": "shaaf@gmail.com", "password": "Shaafiya@123"},
]

for cred in test_credentials:
    print(f"\n📝 Testing: {cred['email']}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/educators/login",
            json={"email": cred['email'], "password": cred['password']}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful!")
            print(f"   Token type: {data.get('token_type')}")
            print(f"   Access token: {data.get('access_token', 'N/A')[:30]}...")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
