"""
Login as Ananya, then fetch filtered students for Section 1.
"""
import requests

BASE_URL = "http://localhost:8003"
EMAIL = "ananya.rao@school.com"
PASSWORD = "Ananya@123"
SECTION_ID = 1

print("Logging in...")
login = requests.post(
    f"{BASE_URL}/api/v1/educators/login",
    data={"username": EMAIL, "password": PASSWORD},
    timeout=10,
)
print("Login status:", login.status_code)
if login.status_code != 200:
    print("Login failed:", login.text)
    raise SystemExit(1)

token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("Fetching filtered students...")
resp = requests.get(
    f"{BASE_URL}/api/v1/students/sections/{SECTION_ID}/students/filtered",
    headers=headers,
    timeout=15,
)
print("Students status:", resp.status_code)
print("Response sample:", resp.text[:400])
