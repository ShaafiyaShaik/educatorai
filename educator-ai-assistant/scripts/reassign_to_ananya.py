#!/usr/bin/env python
"""Reassign imported sections/schedules from educator_id=1 to educator_id=2 (Ananya)."""
import sqlite3

c = sqlite3.connect('educator_db.sqlite')
cur = c.cursor()

# Reassign sections
cur.execute("UPDATE sections SET educator_id=2 WHERE educator_id=1")
sections_updated = cur.rowcount
print(f"Updated {sections_updated} sections to educator_id=2")

# Reassign schedules
cur.execute("UPDATE schedules SET educator_id=2 WHERE educator_id=1")
schedules_updated = cur.rowcount
print(f"Updated {schedules_updated} schedules to educator_id=2")

# Reassign sent_reports
cur.execute("UPDATE sent_reports SET educator_id=2 WHERE educator_id=1")
reports_updated = cur.rowcount
print(f"Updated {reports_updated} sent_reports to educator_id=2")

c.commit()

# Verify
cur.execute("SELECT COUNT(*) FROM sections WHERE educator_id=2")
sec_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM schedules WHERE educator_id=2")
sch_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM sent_reports WHERE educator_id=2")
rep_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM students")
stu_count = cur.fetchone()[0]

print(f"\nVerification:")
print(f"  Sections for educator_id=2: {sec_count}")
print(f"  Schedules for educator_id=2: {sch_count}")
print(f"  Sent_reports for educator_id=2: {rep_count}")
print(f"  Total students (for all sections): {stu_count}")

c.close()

