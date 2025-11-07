"""Search the database for messages containing a given substring.

Run: python e2e_db_search_message.py "Please come to my office"
"""
import sys
from app.core.database import SessionLocal
from app.models.message import Message
from sqlalchemy import desc

def main():
    if len(sys.argv) < 2:
        print("Usage: python e2e_db_search_message.py <substring>")
        sys.exit(2)

    substr = sys.argv[1]
    db = SessionLocal()
    try:
        msgs = db.query(Message).filter(Message.message.like(f"%{substr}%")).order_by(desc(Message.created_at)).all()
        if not msgs:
            print("No matching messages found for substring:", substr)
            return
        for m in msgs:
            print(f"id={m.id} sender_id={m.sender_id} receiver_id={m.receiver_id} subject={m.subject} message={m.message} created_at={m.created_at}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
