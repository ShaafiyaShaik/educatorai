import sqlite3
p = 'D:/Projects/agenticai(3)/educator-ai-assistant/educator_db.sqlite'
print('DB path:', p)
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute("PRAGMA table_info(educators)")
cols = [r[1] for r in cur.fetchall()]
print('columns:', cols)
cur.execute("SELECT id,email,first_name,last_name,hashed_password,is_admin,is_active FROM educators WHERE email=?", ('ananya.rao@school.com',))
row = cur.fetchone()
print('row:', row)
conn.close()