import sqlite3
import os
import shutil
import datetime


def backup_db(db_path):
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    bak = db_path + f'.bak.{ts}'
    shutil.copy2(db_path, bak)
    return bak


def main():
    db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'educator_db.sqlite')
    if not os.path.exists(db):
        print('DB not found:', db)
        return

    bak = backup_db(db)
    print('Backed up DB to', bak)

    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Find duplicate groups using actual column names
    query = '''
    SELECT GROUP_CONCAT(id) as ids
    FROM schedules
    GROUP BY educator_id, title, start_datetime, end_datetime, description, event_type, location
    HAVING COUNT(*) > 1
    '''

    total_deleted = 0
    for (ids,) in cur.execute(query):
        id_list = [int(x) for x in ids.split(',')]
        id_list.sort()
        keep = id_list[0]
        delete = id_list[1:]
        if not delete:
            continue
        q = 'DELETE FROM schedules WHERE id IN ({})'.format(','.join('?' for _ in delete))
        cur.execute(q, delete)
        total_deleted += cur.rowcount

    conn.commit()
    conn.close()

    print('Deleted', total_deleted, 'duplicate schedule rows')


if __name__ == '__main__':
    main()
