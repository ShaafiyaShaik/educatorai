import sqlite3
import os


def main():
    db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'educator_db.sqlite')
    if not os.path.exists(db):
        print('DB not found:', db)
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Group by columns present in this DB's schedules table
    # Use start_datetime and end_datetime (schema uses these names)
    query = '''
    SELECT educator_id, title, start_datetime, end_datetime, description, event_type, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
    FROM schedules
    GROUP BY educator_id, title, start_datetime, end_datetime, description, event_type
    HAVING cnt > 1
    ORDER BY cnt DESC
    LIMIT 200
    '''

    rows = cur.execute(query).fetchall()
    if not rows:
        print('No duplicate schedule groups found.')
        return

    print('Duplicate schedule groups (educator_id, title, start_time, duration, count, ids):')
    for r in rows:
        print(r)

    # Show examples of duplicate rows for the top groups
    top = rows[:5]
    print('\nExample duplicate rows for top groups:')
    for educator_id, title, start_dt, end_dt, description, event_type, cnt, ids in top:
        print('\nGroup:', educator_id, title, start_dt, end_dt, 'event_type=', event_type, 'count=', cnt)
        id_list = [int(x) for x in ids.split(',')]
        q = 'SELECT id, educator_id, title, start_datetime, end_datetime, description, event_type, location FROM schedules WHERE id IN ({}) ORDER BY id'.format(','.join('?' for _ in id_list))
        for row in cur.execute(q, id_list):
            print(row)

    conn.close()


if __name__ == '__main__':
    main()
