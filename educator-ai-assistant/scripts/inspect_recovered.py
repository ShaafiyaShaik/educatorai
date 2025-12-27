import sqlite3, os
p='recovered_72570f92.sqlite'
print('file:', p, 'exists:', os.path.exists(p))
if not os.path.exists(p):
    raise SystemExit('file missing')
print('size', os.path.getsize(p))
conn=sqlite3.connect(p)
cur=conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables:', [r[0] for r in cur.fetchall()])
try:
    cur.execute("SELECT id,email FROM educators LIMIT 10")
    print('educators:', cur.fetchall())
except Exception as e:
    print('educators: error', e)
for t in ('sections','students','schedules','records','messages'):
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t}:', cur.fetchone()[0])
    except Exception as e:
        print(f'{t} error:', e)
conn.close()
