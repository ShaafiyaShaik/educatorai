import requests

# Test exactly what the frontend sends
print("Testing exact frontend login format...")

# Create FormData like the frontend does
formData = {
    'username': 'ananya.rao@school.com',
    'password': 'Ananya@123'
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.post(
    'http://localhost:8003/api/v1/educators/login', 
    data=formData, 
    headers=headers
)

print(f"Status Code: {response.status_code}")
print(f"Headers sent: {headers}")
print(f"Data sent: {formData}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("✅ Login successful!")
    token_data = response.json()
    print(f"Token: {token_data.get('access_token', 'No token')}")
else:
    print("❌ Login failed")
    
# Also test with no explicit Content-Type header (let requests handle it)
print("\n" + "="*50)
print("Testing without explicit Content-Type...")

response2 = requests.post(
    'http://localhost:8003/api/v1/educators/login', 
    data=formData
)

print(f"Status Code: {response2.status_code}")
print(f"Response: {response2.text}")

if response2.status_code == 200:
    print("✅ Login successful!")
    token_data = response2.json()
    print(f"Token: {token_data.get('access_token', 'No token')}")
else:
    print("❌ Login failed")