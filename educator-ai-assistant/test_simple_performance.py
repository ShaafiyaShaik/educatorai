#!/usr/bin/env python3
"""
Simple test script to verify enhanced performance views functionality.
"""

import requests
import json
import os

BASE_URL = "http://127.0.0.1:8001/api/v1"

def login():
    """Login and get access token"""
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/educators/login", data=login_data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def test_performance_views():
    """Test all performance views and reports"""
    
    # Login first
    print("🔐 Logging in...")
    login_response = login()
    if not login_response:
        return
    
    headers = {
        'Authorization': f'Bearer {login_response["access_token"]}',
        'Content-Type': 'application/json'
    }
    print("✅ Login successful!")
    
    # Test 1: Overall Performance
    print("\n📊 Testing Overall Performance...")
    try:
        response = requests.get(f'{BASE_URL}/performance/performance/overview', headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Overall Performance API working!")
            print(f"   📈 Total Sections: {data.get('total_sections', 0)}")
            print(f"   👥 Total Students: {data.get('total_students', 0)}")
            print(f"   📚 Total Subjects: {data.get('total_subjects', 0)}")
            print(f"   🎯 Overall Pass Rate: {data.get('overall_pass_rate', 0)}%")
            print(f"   📊 Overall Average: {data.get('overall_average', 0)}%")
            
            # Test Overall PDF Report
            print("\n📄 Testing Overall PDF Report...")
            pdf_response = requests.get(
                f'{BASE_URL}/performance/performance/reports/download?format=pdf&view_type=overall',
                headers=headers
            )
            if pdf_response.status_code == 200:
                with open('test_overall_report.pdf', 'wb') as f:
                    f.write(pdf_response.content)
                print("✅ Overall PDF report generated: test_overall_report.pdf")
            else:
                print(f"❌ Overall PDF failed: {pdf_response.status_code}")
                try:
                    print(f"   Error: {pdf_response.json()}")
                except:
                    print(f"   Error: {pdf_response.text}")
            
            # Test Overall Excel Report
            print("\n📊 Testing Overall Excel Report...")
            excel_response = requests.get(
                f'{BASE_URL}/performance/performance/reports/download?format=excel&view_type=overall',
                headers=headers
            )
            if excel_response.status_code == 200:
                with open('test_overall_report.xlsx', 'wb') as f:
                    f.write(excel_response.content)
                print("✅ Overall Excel report generated: test_overall_report.xlsx")
            else:
                print(f"❌ Overall Excel failed: {excel_response.status_code}")
                try:
                    print(f"   Error: {excel_response.json()}")
                except:
                    print(f"   Error: {excel_response.text}")
            
            # Test section-specific reports if sections exist
            sections = data.get('sections_summary', [])
            if sections:
                print(f"\n🏫 Testing Section Reports (Found {len(sections)} sections)...")
                first_section = sections[0]
                section_id = first_section.get('section_id')
                section_name = first_section.get('section_name', 'Unknown')
                
                print(f"   Testing Section: {section_name} (ID: {section_id})")
                
                # Test Section PDF
                section_pdf_response = requests.get(
                    f'{BASE_URL}/performance/performance/reports/download?format=pdf&view_type=section&section_id={section_id}',
                    headers=headers
                )
                if section_pdf_response.status_code == 200:
                    with open(f'test_section_{section_id}_report.pdf', 'wb') as f:
                        f.write(section_pdf_response.content)
                    print(f"✅ Section PDF report generated: test_section_{section_id}_report.pdf")
                else:
                    print(f"❌ Section PDF failed: {section_pdf_response.status_code}")
            
            # Test subject-specific reports if subjects exist
            subjects = data.get('subjects_summary', [])
            if subjects:
                print(f"\n📚 Testing Subject Reports (Found {len(subjects)} subjects)...")
                first_subject = subjects[0]
                subject_id = first_subject.get('subject_id')
                subject_name = first_subject.get('subject_name', 'Unknown')
                
                print(f"   Testing Subject: {subject_name} (ID: {subject_id})")
                
                # Test Subject PDF
                subject_pdf_response = requests.get(
                    f'{BASE_URL}/performance/performance/reports/download?format=pdf&view_type=subject&subject_id={subject_id}',
                    headers=headers
                )
                if subject_pdf_response.status_code == 200:
                    with open(f'test_subject_{subject_id}_report.pdf', 'wb') as f:
                        f.write(subject_pdf_response.content)
                    print(f"✅ Subject PDF report generated: test_subject_{subject_id}_report.pdf")
                else:
                    print(f"❌ Subject PDF failed: {subject_pdf_response.status_code}")
                
                # Test Subject Excel
                subject_excel_response = requests.get(
                    f'{BASE_URL}/performance/performance/reports/download?format=excel&view_type=subject&subject_id={subject_id}',
                    headers=headers
                )
                if subject_excel_response.status_code == 200:
                    with open(f'test_subject_{subject_id}_report.xlsx', 'wb') as f:
                        f.write(subject_excel_response.content)
                    print(f"✅ Subject Excel report generated: test_subject_{subject_id}_report.xlsx")
                else:
                    print(f"❌ Subject Excel failed: {subject_excel_response.status_code}")
            
        else:
            print(f"❌ Overall Performance API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error testing performance views: {str(e)}")
        return
    
    print(f"\n🎉 Performance Views Testing Complete!")
    print(f"\n📁 Generated Files:")
    for file in os.listdir('.'):
        if file.startswith('test_') and (file.endswith('.pdf') or file.endswith('.xlsx')):
            size = os.path.getsize(file)
            print(f"   📄 {file} ({size} bytes)")

if __name__ == "__main__":
    test_performance_views()