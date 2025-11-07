#!/usr/bin/env python3
"""
Comprehensive test - API vs Web Request
"""

import sys
sys.path.append('.')

import asyncio
import aiohttp
import json
from app.core.database import get_db
from app.models.educator import Educator
from app.api.performance_views import get_overall_performance

async def test_both_methods():
    print("🔍 COMPREHENSIVE API TEST")
    print("=" * 50)
    
    # Test 1: Direct API function call
    print("1️⃣ DIRECT API FUNCTION CALL")
    print("-" * 30)
    
    db = next(get_db())
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    
    try:
        result = await get_overall_performance(current_educator=shaaf, db=db)
        print(f"✅ Direct API Result:")
        print(f"   Average: {result.overall_average:.1f}%")
        print(f"   Pass Rate: {result.overall_pass_rate:.1f}%")
        print(f"   Students: {result.total_students}")
    except Exception as e:
        print(f"❌ Direct API Error: {e}")
    
    db.close()
    
    # Test 2: HTTP Request (simulating frontend)
    print(f"\n2️⃣ HTTP REQUEST TEST")
    print("-" * 30)
    
    try:
        # Test both localhost and 127.0.0.1
        for host in ['localhost', '127.0.0.1']:
            print(f"\n🌐 Testing {host}:8001...")
            
            async with aiohttp.ClientSession() as session:
                # Login first
                login_data = {
                    'username': 'shaaf@gmail.com',
                    'password': 'password123'
                }
                
                try:
                    async with session.post(f'http://{host}:8001/api/v1/users/login', data=login_data) as response:
                        if response.status == 200:
                            login_result = await response.json()
                            token = login_result['access_token']
                            print(f"   ✅ Login successful")
                            
                            # Test performance API
                            headers = {'Authorization': f'Bearer {token}'}
                            async with session.get(f'http://{host}:8001/api/v1/performance/overview', headers=headers) as perf_response:
                                print(f"   📊 Performance API Status: {perf_response.status}")
                                
                                if perf_response.status == 200:
                                    perf_data = await perf_response.json()
                                    print(f"   ✅ HTTP API Result:")
                                    print(f"      Average: {perf_data.get('overall_average', 'N/A')}%")
                                    print(f"      Pass Rate: {perf_data.get('overall_pass_rate', 'N/A')}%")
                                    print(f"      Students: {perf_data.get('total_students', 'N/A')}")
                                else:
                                    error_text = await perf_response.text()
                                    print(f"   ❌ HTTP API Error: {error_text}")
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Login failed: {response.status} - {error_text}")
                            
                except Exception as e:
                    print(f"   ❌ Connection Error: {e}")
                    
    except Exception as e:
        print(f"❌ HTTP Test Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_both_methods())