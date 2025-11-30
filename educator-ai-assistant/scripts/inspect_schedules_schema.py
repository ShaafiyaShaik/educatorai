import sqlite3
import os


def main():
    db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'educator_db.sqlite')
    if not os.path.exists(db):
        print('DB not found:', db)
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    print('schedules schema:')
    for row in cur.execute("PRAGMA table_info(schedules)"):
        print(row)

    print('\nAll column names in schedules table:')
    cols = [r[1] for r in cur.execute("PRAGMA table_info(schedules)")]
    print(cols)

    sample_cols = cols[:]
    select_cols = ', '.join(sample_cols)
    print('\nSample rows (first 30 rows):')
    try:
        for row in cur.execute(f"SELECT {select_cols} FROM schedules ORDER BY id LIMIT 30"):
            print(row)
    except Exception as e:
        print('Error selecting sample rows:', e)

    conn.close()


if __name__ == '__main__':
    main()
