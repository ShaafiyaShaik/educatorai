"""Seed demo users from `exports/ananya_export.json`.

This script attempts a best-effort, idempotent import of the demo educator
and minimal related data (sections, students). It is intentionally defensive
so it can run on startup in a deployed environment without destroying data.

Usage: set environment variables on the deployed service:
  - `DATABASE_URL` -> your DB connection string
  - `SEED_DEMO_USERS=true` -> to trigger seeding at startup (main.py will call it)

The script will look for `exports/ananya_export.json` at the project root.
"""
from pathlib import Path
import json
import logging

from app.core.database import SessionLocal
from app.core.auth import get_password_hash
from app.models.educator import Educator

logger = logging.getLogger(__name__)


def _load_export():
    root = Path(__file__).resolve().parents[2]
    f = root / 'exports' / 'ananya_export.json'
    if not f.exists():
        logger.info("No exports/ananya_export.json found; skipping seed.")
        return None
    try:
        return json.loads(f.read_text(encoding='utf-8'))
    except Exception as exc:
        logger.exception("Failed to read export file: %s", exc)
        return None


def seed_demo_educators():
    """Idempotently seed demo educator and minimal related rows.

    This function creates demo educators with a known password if they do not
    already exist. It will also attempt to create simple `Section` rows if
    present in the export (best-effort and non-destructive).
    """
    data = _load_export()
    if not data:
        # If no export, still ensure a basic demo educator exists so login works
        _ensure_demo_defaults()
        return

    db = SessionLocal()
    try:
        # Educators
        for ed in data.get('educators', []):
            email = ed.get('email')
            if not email:
                continue
            existing = db.query(Educator).filter(Educator.email == email).first()
            if existing:
                logger.info("Educator %s already exists (id=%s)", email, existing.id)
                # Ensure password is set to a usable known value for demo
                existing.hashed_password = get_password_hash(ed.get('password', 'Ananya@123'))
                db.add(existing)
                db.commit()
                continue
            hashed = get_password_hash(ed.get('password', 'Ananya@123'))
            new = Educator(
                email=email,
                first_name=ed.get('first_name', 'Demo'),
                last_name=ed.get('last_name', 'Educator'),
                hashed_password=hashed,
                is_active=True
            )
            db.add(new)
            db.commit()
            logger.info("Inserted demo educator %s id=%s", email, new.id)

        # Attempt to seed sections if present (best-effort)
        if 'sections' in data:
            try:
                from app.models.section import Section
                for s in data.get('sections', []):
                    title = s.get('title') or s.get('name')
                    if not title:
                        continue
                    # Map owner by email if available
                    owner_email = s.get('educator_email') or (data.get('educators', [])[0].get('email') if data.get('educators') else None)
                    owner = db.query(Educator).filter(Educator.email == owner_email).first() if owner_email else None
                    if not owner:
                        continue
                    exists = db.query(Section).filter(Section.title == title, Section.educator_id == owner.id).first()
                    if exists:
                        continue
                    sec = Section(title=title, educator_id=owner.id)
                    db.add(sec)
                db.commit()
                logger.info("Seeded sections (best-effort)")
            except Exception:
                logger.exception("Failed seeding sections (non-fatal)")

    finally:
        db.close()


def _ensure_demo_defaults():
    """Ensure a minimal demo educator exists even without an export file."""
    DEMO = {"email": "ananya.rao@school.com", "first_name": "Ananya", "last_name": "Rao", "password": "Ananya@123"}
    db = SessionLocal()
    try:
        existing = db.query(Educator).filter(Educator.email == DEMO['email']).first()
        if existing:
            existing.hashed_password = get_password_hash(DEMO['password'])
            db.add(existing)
            db.commit()
            logger.info("Updated existing demo educator %s", DEMO['email'])
            return
        new = Educator(
            email=DEMO['email'],
            first_name=DEMO['first_name'],
            last_name=DEMO['last_name'],
            hashed_password=get_password_hash(DEMO['password']),
            is_active=True
        )
        db.add(new)
        db.commit()
        logger.info("Inserted fallback demo educator %s id=%s", DEMO['email'], new.id)
    finally:
        db.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    seed_demo_educators()
