import requests
import json

# Test registration endpoint
url = "http://127.0.0.1:8001/api/v1/educators/register"
data = {
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "employee_id": "EMP001",
    "department": "Computer Science",
    "title": "Professor",
    "office_location": "Room 101",
    "phone": "+1234567890",
    "password": "testpassword123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")