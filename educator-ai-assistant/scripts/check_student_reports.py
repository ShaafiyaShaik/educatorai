import sys, pathlib
import sqlite3, json, requests
from datetime import timedelta

# Ensure project root is importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.core.auth import create_access_token

DB = 'educator_db.sqlite'
API_BASE = 'http://127.0.0.1:8003'

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT id, email, student_id, first_name, last_name FROM students WHERE first_name LIKE 'Jennifer%' AND last_name LIKE 'Colon%';")
row = cur.fetchone()
if not row:
    print(json.dumps({'error':'Jennifer not found'}))
    exit(1)
student_id, email, sid, first, last = row
print('Found student:', student_id, email)

# Create token
token = create_access_token({'sub': email}, expires_delta=timedelta(minutes=60))
print('Token:', token)

headers = {'Authorization': f'Bearer {token}'}

r = requests.get(f'{API_BASE}/api/v1/student-dashboard/reports', headers=headers)
print('reports status:', r.status_code)
try:
    print(json.dumps(r.json(), indent=2, default=str))
except Exception:
    print(r.text)

r2 = requests.get(f'{API_BASE}/api/v1/student-dashboard/parent-reports', headers=headers)
print('parent-reports status:', r2.status_code)
try:
    print(json.dumps(r2.json(), indent=2, default=str))
except Exception:
    print(r2.text)

conn.close()
