"""Query the database directly to find messages for a student id.

Run: python e2e_db_check.py <student_id>
"""
import sys
from app.core.database import SessionLocal
from app.models.message import Message
from sqlalchemy import desc

def main():
    if len(sys.argv) < 2:
        print("Usage: python e2e_db_check.py <student_id>")
        sys.exit(2)

    student_id = int(sys.argv[1])
    db = SessionLocal()
    try:
        msgs = db.query(Message).filter(Message.receiver_id == student_id).order_by(desc(Message.created_at)).limit(10).all()
        if not msgs:
            print("No messages found for student id", student_id)
            return
        for m in msgs:
            print(f"id={m.id} sender_id={m.sender_id} receiver_id={m.receiver_id} subject={m.subject} message={m.message} created_at={m.created_at}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
