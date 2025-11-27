"""API router for the isolated Simple Gemini Chatbot.

This router is the frontend entrypoint for the simple chatbot. It delegates
intent detection and execution to the server-side `intent_router` service.
It forwards the incoming Authorization header so the service can call the
internal student APIs to resolve names and perform actions.
"""
from typing import Any, Dict
from fastapi import APIRouter, Body, Depends, Request

from app.services.intent_router import detect_and_execute
from app.api.educators import get_current_educator
from app.models.educator import Educator

router = APIRouter()


@router.post("/message")
async def send_message(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    current_educator: Educator = Depends(get_current_educator),
) -> Dict[str, Any]:
    """Accept a JSON payload and route to intent detection + execution.

    Payload keys:
    - message: str (required)
    - history: optional list of {role, content}
    - language: optional language hint
    - auto_execute: optional bool (default true)
    """
    message = payload.get("message", "")
    history = payload.get("history")
    language = payload.get("language", "auto")
    auto_execute = payload.get("auto_execute", True)

    if not message:
        return {"error": "message is required"}

    auth_header = request.headers.get("authorization")

    # Delegate to intent router which will call the model for intent
    # extraction and then perform server-side execution when requested.
    result = await detect_and_execute(
        message=message,
        history=history,
        language=language,
        auto_execute=auto_execute,
        auth_header=auth_header,
        educator_id=current_educator.id,
    )

    return result
    return result
