"""Centralized Action Executor for performing authorized actions against
the internal API server. This module provides a thin safe wrapper around
internal endpoints so callers don't need to duplicate httpx calls and
permission checks.

The implementation is intentionally minimal: it expects an `httpx.AsyncClient`
and forwarded `headers` (including Authorization) and returns normalized
results. Add more permission checks, rate-limiting and auditing hooks as
needed.
"""
from typing import Any, Dict, Optional
import logging
import json

from app.core.database import SessionLocal
from app.models import ActionLog

logger = logging.getLogger(__name__)


async def send_message(client, headers: Dict[str, str], student_id: int, content: str, actor_id: Optional[int] = None) -> Dict[str, Any]:
    payload = {
        "receiver_id": student_id,
        "receiver_type": "student",
        "subject": "Message from educator",
        "message": content,
    }
    try:
        # Use the unified action-engine endpoint
        resp = await client.post("/api/v1/action-engine/send_message", json=payload, headers=headers)
        if resp.status_code in (200, 201):
            data = resp.json()
            # Record audit log (actor_id optional)
            try:
                db = SessionLocal()
                log = ActionLog(
                    actor_id=actor_id,
                    action_type="send_message",
                    target_type="message",
                    target_id=(data.get("id") if isinstance(data, dict) else None),
                    payload=json.dumps({"request": payload, "response": data}),
                )
                db.add(log)
                db.commit()
                db.refresh(log)
            except Exception:
                logger.exception("Failed to write action log for send_message")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            return {"status": "ok", "response": data}
        else:
            return {"status": "error", "detail": f"send_failed:{resp.status_code}", "response": resp.text}
    except Exception as e:
        logger.exception("Exception sending message: %s", e)
        return {"status": "error", "detail": str(e)}


async def schedule_meeting(client, headers: Dict[str, str], student_ids: list, title: str, meeting_date: Optional[str], duration_minutes: int = 60, actor_id: Optional[int] = None) -> Dict[str, Any]:
    payload = {
        "title": title,
        "description": "Scheduled by educator via chatbot",
        "meeting_date": meeting_date,
        "duration_minutes": duration_minutes,
        "meeting_type": "INDIVIDUAL" if len(student_ids) == 1 else "GROUP",
        "student_ids": student_ids,
        "notify_parents": False,
        "send_immediately": True,
    }
    try:
        # Use the unified action-engine endpoint
        resp = await client.post("/api/v1/action-engine/schedule_meeting", json=payload, headers=headers)
        if resp.status_code in (200, 201):
            data = resp.json()
            # audit log for meeting
            try:
                db = SessionLocal()
                log = ActionLog(
                    actor_id=actor_id,
                    action_type="schedule_meeting",
                    target_type="meeting",
                    target_id=(data.get("id") if isinstance(data, dict) else None),
                    payload=json.dumps({"request": payload, "response": data}),
                )
                db.add(log)
                db.commit()
                db.refresh(log)
            except Exception:
                logger.exception("Failed to write action log for schedule_meeting")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            return {"status": "ok", "response": data}
        else:
            return {"status": "error", "detail": f"schedule_failed:{resp.status_code}", "response": resp.text}
    except Exception as e:
        logger.exception("Exception scheduling meeting: %s", e)
        return {"status": "error", "detail": str(e)}


async def fetch_grades(client, headers: Dict[str, str], student_id: int, actor_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        # Grades endpoint remains on students API
        resp = await client.get(f"/api/v1/students/{student_id}/grades", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            try:
                db = SessionLocal()
                log = ActionLog(
                    actor_id=actor_id,
                    action_type="fetch_grades",
                    target_type="grades",
                    target_id=student_id,
                    payload=json.dumps({"response": data}),
                )
                db.add(log)
                db.commit()
                db.refresh(log)
            except Exception:
                logger.exception("Failed to write action log for fetch_grades")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            return {"status": "ok", "response": data}
        else:
            return {"status": "error", "detail": f"fetch_failed:{resp.status_code}", "response": resp.text}
    except Exception as e:
        logger.exception("Exception fetching grades: %s", e)
        return {"status": "error", "detail": str(e)}


async def fetch_schedule(client, headers: Dict[str, str], start_date: str, end_date: str, actor_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        # Schedule fetching remains on scheduling API for now
        resp = await client.get("/api/v1/scheduling/calendar", params={"start_date": start_date, "end_date": end_date}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            try:
                db = SessionLocal()
                log = ActionLog(
                    actor_id=actor_id,
                    action_type="fetch_schedule",
                    target_type="schedule",
                    target_id=None,
                    payload=json.dumps({"start_date": start_date, "end_date": end_date, "response": data}),
                )
                db.add(log)
                db.commit()
                db.refresh(log)
            except Exception:
                logger.exception("Failed to write action log for fetch_schedule")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            return {"status": "ok", "response": data}
        else:
            return {"status": "error", "detail": f"fetch_failed:{resp.status_code}", "response": resp.text}
    except Exception as e:
        logger.exception("Exception fetching schedule: %s", e)
        return {"status": "error", "detail": str(e)}

