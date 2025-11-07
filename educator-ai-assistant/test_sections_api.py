import requests

# Test the sections API
url = "http://localhost:8003/api/v1/students/sections"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sections API working! Found {len(data)} sections:")
        for section in data:
            print(f"  - {section['name']} ({section['academic_year']} - {section['semester']})")
    else:
        print(f"❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server - make sure it's running on port 8003")
except Exception as e:
    print(f"❌ Unexpected error: {e}")