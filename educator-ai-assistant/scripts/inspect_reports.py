import sqlite3, json, sys

DB = 'educator_db.sqlite'

try:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
except Exception as e:
    print(json.dumps({'error': f'Could not open DB {DB}: {e}'}))
    sys.exit(1)

# Find Jennifer Colon
cur.execute("SELECT id, student_id, first_name, last_name FROM students WHERE first_name LIKE 'Jennifer%' AND last_name LIKE 'Colon%';")
students = cur.fetchall()
output = {'students':[]}
for s in students:
    output['students'].append({'id':s[0],'student_id':s[1],'first_name':s[2],'last_name':s[3]})

if students:
    sid = students[0][0]
    cur.execute("SELECT id, title, recipient_type, sent_at, report_format, report_file_path FROM sent_reports WHERE student_id=? ORDER BY sent_at DESC;", (sid,))
    reports = cur.fetchall()
    output['sent_reports'] = []
    for r in reports:
        output['sent_reports'].append({'id':r[0],'title':r[1],'recipient_type':r[2],'sent_at':r[3],'format':r[4],'file_path':r[5]})

    cur.execute("SELECT id, title, message, notification_type, created_at FROM notifications WHERE student_id=? ORDER BY created_at DESC;", (sid,))
    notes = cur.fetchall()
    output['notifications'] = []
    for n in notes:
        output['notifications'].append({'id':n[0],'title':n[1],'message':n[2],'type':n[3],'created_at':n[4]})
else:
    output['sent_reports'] = []
    output['notifications'] = []

print(json.dumps(output, default=str, indent=2))
conn.close()
