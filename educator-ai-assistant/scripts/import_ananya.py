import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime

OUT_EXPORT='exports/ananya_export.json'


def backup_db(path):
    if not os.path.exists(path):
        return None
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    bak = f"{path}.bak.{ts}"
    shutil.copy2(path, bak)
    return bak


def load_export():
    if not os.path.exists(OUT_EXPORT):
        print('Export file not found:', OUT_EXPORT)
        sys.exit(1)
    with open(OUT_EXPORT,'r',encoding='utf-8') as f:
        return json.load(f)


def get_cols(row):
    return list(row.keys())


def insert_row(conn, table, row):
    cur = conn.cursor()
    cols = ','.join(row.keys())
    placeholders = ','.join(['?']*len(row))
    vals = [row[k] for k in row.keys()]
    cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals)
    return cur.lastrowid


def upsert_educator(conn, edu_row):
    cur = conn.cursor()
    # check by email
    cur.execute('select id from educators where email=?', (edu_row['email'],))
    r = cur.fetchone()
    if r:
        return r[0]
    # insert minimal columns to avoid schema mismatches
    cols = ['email','first_name','last_name','employee_id','department','title','office_location','phone','hashed_password','is_active','is_admin','timezone','created_at','last_login']
    data = {k: edu_row.get(k) for k in cols if k in edu_row}
    # ensure required fields
    if 'hashed_password' not in data or not data.get('hashed_password'):
        data['hashed_password'] = 'imported'
    cur.execute('INSERT INTO educators ('+','.join(data.keys())+') VALUES ('+','.join(['?']*len(data))+')', tuple(data.values()))
    conn.commit()
    return cur.lastrowid


def upsert_section(conn, section_row, edu_new_id, section_map):
    cur = conn.cursor()
    # match by name and educator_id
    cur.execute('select id from sections where name=? and educator_id=?', (section_row['name'], edu_new_id))
    r = cur.fetchone()
    if r:
        section_map[section_row['id']] = r[0]
        return r[0]
    # insert
    data = {k: section_row.get(k) for k in ['id','name','educator_id','academic_year','semester','created_at','updated_at'] if k in section_row}
    # remove id to let db assign new one
    if 'id' in data: del data['id']
    cur.execute('INSERT INTO sections ('+','.join(data.keys())+') VALUES ('+','.join(['?']*len(data))+')', tuple(data.values()))
    conn.commit()
    newid = cur.lastrowid
    section_map[section_row['id']] = newid
    return newid


def upsert_student(conn, student_row, section_map, student_map):
    cur = conn.cursor()
    # check by email
    cur.execute('select id from students where email=?', (student_row['email'],))
    r = cur.fetchone()
    if r:
        student_map[student_row['id']] = r[0]
        return r[0]
    # prepare data
    data = {}
    for k in ['student_id','first_name','last_name','email','password_hash','roll_number','section_id','phone','date_of_birth','address','guardian_email','is_active','created_at','updated_at']:
        if k in student_row:
            data[k] = student_row[k]
    # remap section_id
    if 'section_id' in data and data['section_id'] in section_map:
        data['section_id'] = section_map[data['section_id']]
    # remove id to let db assign
    if 'id' in data: del data['id']
    cols = ','.join(data.keys())
    vals = tuple(data.values())
    cur.execute('INSERT INTO students ('+cols+') VALUES ('+','.join(['?']*len(vals))+')', vals)
    conn.commit()
    newid = cur.lastrowid
    student_map[student_row['id']] = newid
    return newid


def remap_and_insert_generic(conn, table, rows, section_map, student_map, edu_map):
    cur = conn.cursor()
    inserted = 0
    for row in rows:
        r = dict(row)
        # remap ids
        if 'educator_id' in r and r['educator_id'] in edu_map:
            r['educator_id'] = edu_map[r['educator_id']]
        if 'section_id' in r and r['section_id'] in section_map:
            r['section_id'] = section_map[r['section_id']]
        if 'student_id' in r and r['student_id'] in student_map:
            r['student_id'] = student_map[r['student_id']]
        # avoid inserting duplicate sent_reports: check by educator_id, student_id, created_at, title if exist
        try:
            if table=='sent_reports':
                cur.execute('select id from sent_reports where educator_id=? and student_id=? and created_at=? and title=?', (r.get('educator_id'), r.get('student_id'), r.get('created_at'), r.get('title')))
                if cur.fetchone():
                    continue
            # remove id to let sqlite assign
            if 'id' in r: del r['id']
            cols = ','.join(r.keys())
            vals = tuple(r.values())
            cur.execute(f'INSERT INTO {table} ('+cols+') VALUES ('+','.join(['?']*len(vals))+')', vals)
            inserted += 1
        except Exception as e:
            # skip rows that fail due to schema differences
            # print('Failed insert', table, e)
            continue
    conn.commit()
    return inserted


def main():
    export = load_export()
    targets = [os.path.join('..','educator_db.sqlite'), os.path.join('app','educator_db.sqlite')]
    for tgt in targets:
        print('\n==== Importing into', tgt, '====')
        bak = backup_db(tgt)
        if bak:
            print('Backed up', tgt, '->', bak)
        else:
            print('No existing DB to backup at', tgt)
        conn = sqlite3.connect(tgt)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        edu_row = export['data'].get('educators',[None])[0]
        if not edu_row:
            print('No educator in export?')
            conn.close(); continue
        # mapping dicts
        edu_map = {}
        section_map = {}
        student_map = {}
        # upsert educator
        new_edu_id = upsert_educator(conn, edu_row)
        edu_map[edu_row['id']] = new_edu_id
        print('Educator mapped old->new', edu_row['id'], '->', new_edu_id)
        # upsert sections
        for s in export['data'].get('sections',[]):
            upsert_section(conn, s, new_edu_id, section_map)
        print('Sections mapped:', section_map)
        # upsert students
        for st in export['data'].get('students',[]):
            upsert_student(conn, st, section_map, student_map)
        print('Students mapped count:', len(student_map))
        # other tables
        for table in ['schedules','sent_reports','notifications','messages','meetings','records']:
            rows = export['data'].get(table, [])
            if not rows:
                continue
            ins = remap_and_insert_generic(conn, table, rows, section_map, student_map, edu_map)
            print(f'Inserted {ins} rows into {table}')
        conn.close()
    print('\nImport complete')

if __name__=='__main__':
    main()
