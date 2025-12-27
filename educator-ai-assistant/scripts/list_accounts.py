import os
import sqlite3

DB_CANDIDATES = ["educator_db.sqlite", os.path.join("app","educator_db.sqlite")]

def inspect_db(path):
    print('\n--- DB file:', path, '---')
    if not os.path.exists(path):
        print('MISSING')
        return
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    def safe_query(q):
        try:
            return cur.execute(q).fetchall()
        except Exception as e:
            return f'ERROR: {e}'

    # Educators
    eds = safe_query("select id, email, first_name, last_name from educators")
    if isinstance(eds, str):
        print('Educators query error:', eds)
    else:
        print('Educators count:', len(eds))
        for r in eds[:200]:
            print('E:', r)

    # Students
    studs = safe_query("select id, email, first_name, last_name from students")
    if isinstance(studs, str):
        print('Students query error:', studs)
    else:
        print('Students count:', len(studs))
        for r in studs[:200]:
            print('S:', r)

    # Basic cross-check: list sections with educator_id
    secs = safe_query("select id, name, educator_id from sections")
    if isinstance(secs, str):
        print('Sections query error:', secs)
    else:
        print('Sections count:', len(secs))
        for r in secs[:200]:
            print('Sec:', r)

    conn.close()

if __name__ == '__main__':
    cwd = os.getcwd()
    print('CWD:', cwd)
    for p in DB_CANDIDATES:
        # try absolute path relative to cwd
        inspect_db(os.path.join(cwd, p) if not os.path.isabs(p) else p)
    print('\nDone.')
