#!/usr/bin/env python3
"""
Simple debug test 
"""

import requests

BASE_URL = "http://127.0.0.1:8001"

def simple_test():
    response = requests.post(f"{BASE_URL}/api/v1/assistant/test-command", json={
        "command": "hello",
        "language": "en",
        "mode": "assist"
    })
    
    print("Response:", response.json())

if __name__ == "__main__":
    simple_test()