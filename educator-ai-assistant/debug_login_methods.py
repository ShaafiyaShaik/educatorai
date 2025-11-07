import requests
from requests.auth import HTTPBasicAuth

# Test different request methods
print("Testing different login request methods...\n")

# Method 1: Using form data (what we tried before)
print("1. Form data method:")
login_data = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}
response = requests.post('http://localhost:8003/api/v1/educators/login', data=login_data)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:100]}")

# Method 2: Using JSON (what frontend might be sending)  
print("\n2. JSON method:")
login_json = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}
response = requests.post('http://localhost:8003/api/v1/educators/login', json=login_json)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:100]}")

# Method 3: Check what the exact frontend sends
print("\n3. Check server logs or add debug to understand exact request...")

# Method 4: Manual form encoding
print("\n4. Manual form encoding:")
import urllib.parse
form_data = urllib.parse.urlencode({
    'username': 'ananya.rao@school.com',
    'password': 'Ananya@123'
})
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
response = requests.post('http://localhost:8003/api/v1/educators/login', 
                        data=form_data, headers=headers)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:100]}")