"""
Debug Performance Issues
"""
import requests
import traceback

def debug_performance():
    """Debug the performance endpoint step by step"""
    
    # Step 1: Login
    print("🔐 Step 1: Login")
    login_data = {
        'username': 'shaafiya07@gmail.com',  # This educator has sections
        'password': 'password123'
    }
    
    try:
        login_response = requests.post('http://localhost:8001/api/v1/educators/login', data=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
            
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print(f"✅ Login successful! Token: {token[:20]}...")
        
        # Step 2: Check sections first
        print("\n📚 Step 2: Check sections")
        sections_response = requests.get('http://localhost:8001/api/v1/students/sections', headers=headers)
        print(f"Sections Status: {sections_response.status_code}")
        if sections_response.status_code == 200:
            sections = sections_response.json()
            print(f"Found {len(sections)} sections")
        else:
            print(f"Sections Error: {sections_response.text}")
        
        # Step 3: Test performance endpoint
        print("\n📊 Step 3: Test performance endpoint")
        perf_response = requests.get('http://localhost:8001/api/v1/performance/overview', headers=headers, timeout=30)
        print(f"Performance Status: {perf_response.status_code}")
        
        if perf_response.status_code == 200:
            data = perf_response.json()
            print("✅ Performance endpoint working!")
            print(f"Total sections: {data.get('total_sections', 0)}")
            print(f"Total students: {data.get('total_students', 0)}")
            print(f"Overall average: {data.get('overall_average', 0)}%")
            print(f"Pass rate: {data.get('overall_pass_rate', 0)}%")
        else:
            print(f"❌ Performance error: {perf_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_performance()