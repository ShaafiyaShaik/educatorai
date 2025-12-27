"""
Test educator login using OAuth2 form data.
"""
import requests

BASE_URL = "http://localhost:8003"
EMAIL = "ananya.rao@school.com"
PASSWORD = "Ananya@123"

print("Testing login...")
resp = requests.post(
    f"{BASE_URL}/api/v1/educators/login",
    data={"username": EMAIL, "password": PASSWORD},
    timeout=10,
)
print("Status:", resp.status_code)
print("Body:", resp.text[:200])
if resp.status_code == 200:
    data = resp.json()
    print("Token type:", data.get("token_type"))
    print("Token (prefix):", (data.get("access_token") or "")[:32])
else:
    print("Login failed.")
