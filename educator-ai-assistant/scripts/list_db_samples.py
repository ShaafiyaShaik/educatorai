import sqlite3
p = 'D:/Projects/agenticai(3)/educator-ai-assistant/educator_db.sqlite'
print('Using DB:', p)
conn = sqlite3.connect(p)
cur = conn.cursor()

def fetch(name, qry):
    print('\n--', name)
    try:
        cur.execute(qry)
        rows = cur.fetchall()
        for r in rows[:20]:
            print(' ', r)
    except Exception as e:
        print('  error:', e)

# show educators
fetch('educators', "SELECT id, email, first_name, last_name FROM educators LIMIT 20")
# sections
fetch('sections', "SELECT id, name, educator_id FROM sections LIMIT 20")
# students
fetch('students', "SELECT id, first_name, last_name, section_id FROM students LIMIT 20")
# schedules
fetch('schedules', "SELECT id, title, educator_id, start_time FROM schedules LIMIT 20")
# records
fetch('records', "SELECT id, student_id, educator_id, summary FROM records LIMIT 20")
conn.close()
