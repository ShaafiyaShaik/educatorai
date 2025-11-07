import requests
import json

# Test the teacher login
login_data = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}

print("Testing teacher login...")
response = requests.post('http://localhost:8003/api/v1/educators/login', data=login_data)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    token_data = response.json()
    print(f"✅ Login successful! Token: {token_data.get('access_token', 'No token')}")
else:
    print(f"❌ Login failed: {response.text}")