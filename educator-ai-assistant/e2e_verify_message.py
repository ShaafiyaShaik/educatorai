"""Verify that a message was created for the resolved student.

This script will:
 - GET /api/v1/bulk-communication/students and search for a student named Jennifer
 - If found, GET /api/v1/messages/sent?student_id=<id> to list messages sent to that student

Run: python e2e_verify_message.py
"""
import requests
import sys

BASE = "http://127.0.0.1:8003"

def get_students():
    try:
        r = requests.get(f"{BASE}/api/v1/bulk-communication/students", timeout=10)
        r.raise_for_status()
        return r.json().get("students") if isinstance(r.json(), dict) and r.json().get("students") is not None else r.json()
    except Exception as e:
        print("Failed to get students:", e)
        return []

def find_student_by_name(students, name):
    lname = name.lower().strip()
    for s in students:
        nm = s.get("name") or f"{s.get('first_name','')} {s.get('last_name','')}".strip()
        if nm and lname in nm.lower():
            return s
    return None

def get_sent_messages(student_id):
    try:
        r = requests.get(f"{BASE}/api/v1/messages/sent", params={"student_id": student_id}, timeout=10)
        print("GET /api/v1/messages/sent status:", r.status_code)
        print(r.text)
    except Exception as e:
        print("Failed to list sent messages:", e)

def main():
    students = get_students()
    if not students:
        print("No students returned from bulk-communication/students")
        sys.exit(2)

    student = find_student_by_name(students, "Jennifer")
    if not student:
        print("Could not find a student named 'Jennifer' in students list. Sample names:")
        for s in students[:10]:
            print(s.get('name') or f"{s.get('first_name')} {s.get('last_name')}")
        sys.exit(3)

    print("Found student:", student)
    sid = student.get("id") or student.get("student_id")
    if not sid:
        print("Student record has no id field, raw record printed above.")
        sys.exit(4)

    print("Checking sent messages for student id:", sid)
    get_sent_messages(sid)

if __name__ == '__main__':
    main()
