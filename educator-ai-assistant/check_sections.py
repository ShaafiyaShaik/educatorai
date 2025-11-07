#!/usr/bin/env python3
"""
Check which teachers have sections
"""
from app.core.database import SessionLocal
from app.models.student import Section
from app.models.educator import Educator

def check_sections():
    db = SessionLocal()
    sections = db.query(Section).all()
    print('Sections in database:')
    for section in sections:
        educator = db.query(Educator).filter(Educator.id == section.educator_id).first()
        print(f'Section: {section.name}, Teacher: {educator.email if educator else "Unknown"}')
    db.close()

if __name__ == "__main__":
    check_sections()