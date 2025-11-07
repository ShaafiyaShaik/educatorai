#!/usr/bin/env python3

import requests
import json

def test_api_call():
    """Test the actual API call to see what's happening"""
    
    # Test data
    test_data = {
        "command": "hey",
        "language": "en",
        "mode": "assist",
        "educator_id": 1
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8001/api/v1/assistant/command",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server first.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_call()