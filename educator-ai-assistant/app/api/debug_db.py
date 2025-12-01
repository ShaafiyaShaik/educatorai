"""
Temporary admin debug endpoints for checking which database the app is using.

This file is safe to remove after debugging deployment issues. It exposes
an admin-only route `/api/v1/admin/debug-db` (no auth) to help confirm the
runtime `settings.DATABASE_URL`, whether the referenced SQLite file exists,
and a quick check for the demo educator email used in the recovery steps.
"""
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core.database import get_db
from sqlalchemy.orm import Session
import os

from app.models.educator import Educator

router = APIRouter()


@router.get("/debug-db")
def debug_db_status():
    """Return runtime DB info without requiring a DB session (safe to call).

    This endpoint is intentionally simple so it can be called when diagnosing
    deployed instances where pulling logs or dashboard envs is slower.
    """
    info = {"database_url": settings.DATABASE_URL}
    # If using SQLite, report whether the file exists and its absolute path
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite:"):
        # sqlite:///./app/educator_db.sqlite -> ./app/educator_db.sqlite
        path = settings.DATABASE_URL.replace("sqlite:///", "")
        info["sqlite_path"] = os.path.abspath(path)
        info["sqlite_exists"] = os.path.exists(path)
    else:
        info["sqlite_path"] = None
        info["sqlite_exists"] = False
    return info


@router.get("/debug-db/educator")
def debug_db_educator():
    """Query the DB for basic educator info (requires DB access).

    This route attempts a lightweight DB connection and returns whether the
    demo educator `ananya.rao@school.com` exists and how many educators total.
    """
    try:
        db = next(get_db())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB session error: {exc}")

    try:
        total = db.query(Educator).count()
        ananya = db.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        return {
            "total_educators": total,
            "ananya_present": bool(ananya),
            "ananya_id": ananya.id if ananya else None,
            "ananya_email": ananya.email if ananya else None,
        }
    finally:
        db.close()
