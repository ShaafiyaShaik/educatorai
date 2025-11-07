"""API router for the isolated Simple Gemini Chatbot.

This router provides a single endpoint that the frontend can call to send
messages to the SimpleGeminiChatbot. It is intentionally isolated from the
project's previous assistant endpoints.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, Request
import httpx
import logging

from app.agents.simple_gemini_chatbot import simple_chatbot
from app.api.educators import get_current_educator
from app.models.educator import Educator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message")
async def send_message(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    current_educator: Educator = Depends(get_current_educator),
):
    """Accept a JSON payload with keys:
    - message: str
    - history: optional list of {role, content}
    - language: optional language hint
    - auto_execute: optional bool (default true)

    The endpoint will forward the incoming Authorization header when calling
    internal APIs to perform actions (send_message, schedule_meeting) on behalf
    of the authenticated educator.
    """
    message = payload.get("message", "")
    history = payload.get("history")
    language = payload.get("language", "auto")
    auto_execute = payload.get("auto_execute", True)

    if not message:
        return {"error": "message is required"}

    # Ask the chatbot for a reply and detected action (do not auto-execute there)
    result = simple_chatbot.chat(message=message, history=history, language=language, auto_execute=False)

    action = result.get("action")
    executed = None

    if action and auto_execute:
        auth_header = request.headers.get("authorization")

        async with httpx.AsyncClient(base_url="http://127.0.0.1:8003") as client:
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            act = action.get("action")

            async def resolve_student_by_name(name: str) -> Optional[int]:
                """Try multiple strategies to resolve a student name to an ID."""
                if not name:
                    return None
                try:
                    # 1) Get bulk students list
                    resp = await client.get("/api/v1/bulk-communication/students", headers=headers)
                    if resp.status_code == 200:
                        students = resp.json().get("students", [])
                        lname = name.lower().strip()
                        # Exact match full name
                        for s in students:
                            if s.get("name") and s.get("name").lower().strip() == lname:
                                return s.get("id")
                        # Partial match (first or last)
                        for s in students:
                            if s.get("name") and lname in s.get("name").lower():
                                return s.get("id")

                    # 2) Try students endpoint that supports section filter/search
                    resp2 = await client.get("/api/v1/students", headers=headers)
                    if resp2.status_code == 200:
                        data = resp2.json()
                        students2 = data.get("students") if isinstance(data, dict) else data
                        if students2:
                            for s in students2:
                                if s.get("name") and name.lower().strip() in s.get("name").lower():
                                    return s.get("id")
                except Exception as e:
                    logger.exception("Error resolving student name '%s': %s", name, e)
                return None

            try:
                if act == "send_message":
                    recipient = action.get("recipient")
                    content = action.get("content")

                    student_id = None
                    # If recipient looks like an ID
                    try:
                        maybe_id = int(recipient)
                        student_id = maybe_id
                    except Exception:
                        student_id = await resolve_student_by_name(recipient)

                    logger.info("Resolved recipient '%s' to student_id=%s", recipient, student_id)

                    if student_id is None:
                        executed = {"status": "error", "detail": "Recipient not found"}
                    else:
                        msg_payload = {
                            "receiver_id": student_id,
                            "receiver_type": "student",
                            "subject": "Message from educator",
                            "message": content,
                        }
                        resp = await client.post("/api/v1/messages/send", json=msg_payload, headers=headers)
                        logger.info("Internal send message response: %s %s", resp.status_code, resp.text)
                        if resp.status_code in (200, 201):
                            executed = {"status": "ok", "detail": f"Message sent to {recipient}", "response": resp.json()}
                        else:
                            executed = {"status": "error", "detail": f"Failed to send message: {resp.status_code}", "response": resp.text}

                elif act == "schedule_meeting":
                    recipient = action.get("recipient")
                    dt = action.get("datetime")

                    student_id = await resolve_student_by_name(recipient)
                    logger.info("Resolved recipient '%s' to student_id=%s for meeting", recipient, student_id)

                    if student_id is None:
                        executed = {"status": "error", "detail": "Recipient not found"}
                    else:
                        meeting_payload = {
                            "title": f"Meeting with {recipient}",
                            "description": "Scheduled by educator via chatbot",
                            "meeting_date": dt,
                            "duration_minutes": 60,
                            "meeting_type": "INDIVIDUAL",
                            "student_ids": [student_id],
                            "notify_parents": False,
                            "send_immediately": True
                        }
                        resp = await client.post("/api/v1/meetings/", json=meeting_payload, headers=headers)
                        logger.info("Internal schedule meeting response: %s %s", resp.status_code, resp.text)
                        if resp.status_code in (200, 201):
                            executed = {"status": "ok", "detail": f"Meeting scheduled with {recipient}", "response": resp.json()}
                        else:
                            executed = {"status": "error", "detail": f"Failed to schedule meeting: {resp.status_code}", "response": resp.text}

                else:
                    executed = {"status": "error", "detail": "Unknown action"}
            except Exception as e:
                logger.exception("Error executing action %s: %s", act, e)
                executed = {"status": "error", "detail": str(e)}

    return {**result, "action": action, "executed": executed}
"""API router for the isolated Simple Gemini Chatbot.

This router provides a single endpoint that the frontend can call to send
messages to the SimpleGeminiChatbot. It is intentionally isolated from the
project's previous assistant endpoints.
"""
from typing import Any, Dict
from fastapi import APIRouter, Body, Depends, Request
import httpx
import logging

from app.agents.simple_gemini_chatbot import simple_chatbot
from app.api.educators import get_current_educator
from app.models.educator import Educator
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message")
async def send_message(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    current_educator: Educator = Depends(get_current_educator),
):
    """Accept a JSON payload with keys:
    - message: str
    - history: optional list of {role, content}
    - language: optional language hint
    - auto_execute: optional bool (default true)

    The endpoint will forward the incoming Authorization header when calling
    internal APIs to perform actions (send_message, schedule_meeting) on behalf
    of the authenticated educator.
    """
    message = payload.get("message", "")
    history = payload.get("history")
    language = payload.get("language", "auto")
    auto_execute = payload.get("auto_execute", True)

    if not message:
        return {"error": "message is required"}

    # Ask the chatbot for a reply and detected action (do not auto-execute there)
    result = simple_chatbot.chat(message=message, history=history, language=language, auto_execute=False)

    action = result.get("action")
    if action and auto_execute:
        auth_header = request.headers.get("authorization")

        async with httpx.AsyncClient(base_url="http://127.0.0.1:8003") as client:
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            act = action.get("action")
            try:
                if act == "send_message":
                    recipient = action.get("recipient")
                    content = action.get("content")

                    student_id = None
                    # If recipient looks like an ID
                    try:
                        maybe_id = int(recipient)
                        student_id = maybe_id
                    except Exception:
                        # Resolve recipient by name using students list endpoint
                        students_resp = await client.get("/api/v1/bulk-communication/students", headers=headers)
                        if students_resp.status_code == 200:
                            students = students_resp.json().get("students", [])
                            for s in students:
                                if recipient and recipient.lower() in s.get("name", "").lower():
                                    student_id = s.get("id")
                                    break

                    logger.info("Resolved recipient '%s' to student_id=%s", recipient, student_id)

                    if student_id is None:
                        executed = {"status": "error", "detail": "Recipient not found"}
                    else:
                        msg_payload = {
                            "receiver_id": student_id,
                            "receiver_type": "student",
                            "subject": "Message from educator",
                            "message": content,
                        }
                        resp = await client.post("/api/v1/messages/send", json=msg_payload, headers=headers)
                        logger.info("Internal send message response: %s %s", resp.status_code, resp.text)
                        if resp.status_code in (200, 201):
                            executed = {"status": "ok", "detail": f"Message sent to {recipient}", "response": resp.json()}
                        else:
                            executed = {"status": "error", "detail": f"Failed to send message: {resp.status_code}", "response": resp.text}

                elif act == "schedule_meeting":
                    recipient = action.get("recipient")
                    dt = action.get("datetime")

                    student_id = await resolve_student_by_name(recipient)
                    logger.info("Resolved recipient '%s' to student_id=%s for meeting", recipient, student_id)

                    if student_id is None:
                        executed = {"status": "error", "detail": "Recipient not found"}
                    else:
                        meeting_payload = {
                            "title": f"Meeting with {recipient}",
                            "description": "Scheduled by educator via chatbot",
                            "meeting_date": dt,
                            "duration_minutes": 60,
                            "meeting_type": "INDIVIDUAL",
                            "student_ids": [student_id],
                            "notify_parents": False,
                            "send_immediately": True
                        }
                        resp = await client.post("/api/v1/meetings/", json=meeting_payload, headers=headers)
                        logger.info("Internal schedule meeting response: %s %s", resp.status_code, resp.text)
                        if resp.status_code in (200, 201):
                            executed = {"status": "ok", "detail": f"Meeting scheduled with {recipient}", "response": resp.json()}
                        else:
                            executed = {"status": "error", "detail": f"Failed to schedule meeting: {resp.status_code}", "response": resp.text}

                else:
                    executed = {"status": "error", "detail": "Unknown action"}
            except Exception as e:
                logger.exception("Error executing action %s: %s", act, e)
                executed = {"status": "error", "detail": str(e)}
            except Exception as e:
                executed = {"status": "error", "detail": str(e)}

    return {**result, "action": action, "executed": executed}
"""API router for the isolated Simple Gemini Chatbot.

This router provides a single endpoint that the frontend can call to send
messages to the SimpleGeminiChatbot. It is intentionally isolated from the
project's previous assistant endpoints.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body

from app.agents.simple_gemini_chatbot import simple_chatbot

router = APIRouter()


@router.post("/message")
def send_message(
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """Accept a JSON payload with keys:
    - message: str
    - history: optional list of {role, content}
    - language: optional language hint
    - auto_execute: optional bool (default true)

    Returns the Gemini reply plus optional action and execution status.
    """
    message = payload.get("message", "")
    history = payload.get("history")
    language = payload.get("language", "auto")
    auto_execute = payload.get("auto_execute", True)

    if not message:
        return {"error": "message is required"}

    result = simple_chatbot.chat(message=message, history=history, language=language, auto_execute=auto_execute)
    return result
