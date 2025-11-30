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
    before = cur.execute('SELECT COUNT(*) FROM schedules').fetchone()[0]

    # Delete duplicate rows, keeping the row with the minimum id per group
    delete_sql = '''
    DELETE FROM schedules
    WHERE id NOT IN (
      SELECT MIN(id) FROM schedules
      GROUP BY educator_id, title, start_datetime, end_datetime, description, event_type, location
    )
    '''

    cur.execute(delete_sql)
    conn.commit()
    after = cur.execute('SELECT COUNT(*) FROM schedules').fetchone()[0]
    deleted = before - after
    conn.close()

    print('Deleted', deleted, 'duplicate schedule rows (via SQL)')


if __name__ == '__main__':
    main()
