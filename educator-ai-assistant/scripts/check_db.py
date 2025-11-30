import sqlite3
import os


def main():
    db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'educator_db.sqlite')
    if not os.path.exists(db):
        print('DB not found:', db)
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    print('educators:')
    for row in cur.execute('select id, email, first_name, last_name from educators'):
        print(row)
    print('\nsections:')
    for row in cur.execute('select id, name, educator_id from sections order by id'):
        print(row)
    conn.close()


if __name__ == '__main__':
    main()
