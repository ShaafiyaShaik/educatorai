import requests
import json

# Login
login_data = {
    'username': 'shaaf@gmail.com',
    'password': 'password123'
}

login_resp = requests.post('http://127.0.0.1:8001/api/v1/educators/login', data=login_data)
print(f"Login Status: {login_resp.status_code}")

if login_resp.status_code == 200:
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test overview endpoint first
    print("\nTesting overview endpoint...")
    resp = requests.get('http://127.0.0.1:8001/api/v1/performance/performance/overview', headers=headers)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("Overview data retrieved successfully!")
        print(f"Sections: {data.get('total_sections')}")
        print(f"Students: {data.get('total_students')}")
        
        # Now test PDF report
        print("\nTesting PDF report...")
        resp = requests.get('http://127.0.0.1:8001/api/v1/performance/performance/reports/download?format=pdf&view_type=overall', headers=headers)
        print(f"PDF Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"PDF Error Response: {resp.text}")
            
            # Try to get more details from response
            try:
                error_data = resp.json()
                print(f"PDF Error Details: {json.dumps(error_data, indent=2)}")
            except:
                pass
    else:
        print(f"Overview Error Response: {resp.text}")
else:
    print("Login failed")