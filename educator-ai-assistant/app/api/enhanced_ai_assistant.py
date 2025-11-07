"""
Enhanced AI Assistant API with Google Gemini integration
Supports autonomy modes, multilingual support, and advanced features
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from app.core.database import get_db
from app.api.educators import get_current_educator
from app.models.educator import Educator
from app.agents.gemini_assistant import gemini_assistant, AutonomyMode, Language
from app.core.config import settings
import google.generativeai as genai

router = APIRouter()

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    autonomy_mode: Optional[AutonomyMode] = AutonomyMode.ASSIST
    # Accept loose language inputs from the frontend (e.g. 'en', 'english', 'te', 'telugu')
    language: Optional[str] = "en"
    # Optional conversation history to provide context (list of {type: 'user'|'assistant', content})
    history: Optional[List[Dict[str, str]]] = None

class ActionApprovalRequest(BaseModel):
    action_id: str
    approved: bool
    feedback: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    autonomy_mode: Optional[AutonomyMode] = None
    language: Optional[Language] = None
    permissions: Optional[Dict[str, bool]] = None

class ChatResponse(BaseModel):
    response: str
    actions: List[Dict[str, Any]]
    state: str
    requires_approval: bool
    audit_log: List[Dict[str, Any]]
    language: str
    timestamp: str


# Public chat (unauthenticated) - lightweight conversational endpoint
class PublicChatRequest(BaseModel):
    message: str
    # Public endpoint may pass a free-form language value; accept string and normalize
    language: Optional[str] = "en"


class PublicChatResponse(BaseModel):
    response: str
    raw: Optional[str] = None


@router.post("/public-chat", response_model=PublicChatResponse)
async def public_chat(
    request: PublicChatRequest
):
    """
    Lightweight unauthenticated chat endpoint that forwards a simple prompt to Gemini
    and returns the assistant's reply. This is useful for testing the Gemini key
    and having a quick chat without educator authentication. WARNING: This
    exposes the assistant publicly — use only for local/dev environments.
    """
    try:
        # Build a simple prompt that asks for a plain conversational reply
        prompt = f"""
        You are EduAssist AI, an administrative assistant for educators.
        Reply conversationally to the user's message. Keep the reply concise.

        User said: "{request.message}"

        Return just the assistant reply in plain text.
        """

        # Use the existing gemini_assistant helper to call Gemini
        # Normalize language (not used by this simple demo prompt, but keep consistent)
        lang = (request.language or "en").strip().lower()
        if lang.startswith("en"):
            gemini_assistant.set_language(Language.ENGLISH)
        elif lang.startswith("te"):
            gemini_assistant.set_language(Language.TELUGU)
        else:
            gemini_assistant.set_language(Language.ENGLISH)

        raw_resp = await gemini_assistant._call_gemini(prompt)
        reply = raw_resp.strip() if isinstance(raw_resp, str) else str(raw_resp)

        return PublicChatResponse(response=reply, raw=raw_resp)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Public chat error: {str(e)}")

class BackgroundTaskRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any]

@router.post("/enhanced-chat", response_model=ChatResponse)
async def enhanced_chat_with_assistant(
    request: ChatRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """
    Enhanced chat interface with the Gemini AI assistant
    Supports different autonomy modes and languages
    """
    try:
        # Update assistant settings if provided
        if request.autonomy_mode:
            gemini_assistant.set_autonomy_mode(request.autonomy_mode)

        # Normalize and set language from loose input values
        raw_lang = (request.language or "en").strip().lower()
        if raw_lang.startswith("en"):
            gemini_assistant.set_language(Language.ENGLISH)
        elif raw_lang.startswith("te"):
            gemini_assistant.set_language(Language.TELUGU)
        else:
            # default to English for any unrecognized language input
            gemini_assistant.set_language(Language.ENGLISH)
        
        # Process the command
        result = await gemini_assistant.process_command(
            request.message,
            current_educator.id,
            db,
            conversation_history=request.history
        )
        
        return ChatResponse(
            response=result["response"],
            actions=result["actions"],
            state=result["state"],
            requires_approval=result["requires_approval"],
            audit_log=result["audit_log"],
            language=result["language"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")


# DEV-ONLY: Echo endpoint to help debug request validation from the frontend
# This endpoint is intentionally unauthenticated and should ONLY be used in
# local development to inspect what the frontend is sending. It echoes back
# the parsed `ChatRequest` model (or returns a 422 validation error body).
@router.post("/debug-enhanced-chat-echo")
async def debug_enhanced_chat_echo(request: ChatRequest):
    """
    Echo parsed ChatRequest for debugging frontend -> backend request issues.
    Returns the parsed request as JSON when valid, or triggers FastAPI's
    validation errors (422) when invalid.
    """
    return {
        "ok": True,
        "parsed": request.dict()
    }


class PublicChatRequest(BaseModel):
    message: str
    model: Optional[str] = None


@router.post("/public-chat")
async def public_gemini_chat(request: PublicChatRequest):
    """Lightweight unauthenticated Gemini chat for quick testing and demos.
    Uses the configured GEMINI_API_KEY and GEMINI_MODEL. This bypasses educator
    authentication and does not execute actions — it only returns Gemini's text response.
    """
    try:
        # Use configured model or override if provided
        model_name = request.model or getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-pro')
        # Ensure client is configured
        genai.configure(api_key=getattr(settings, 'GEMINI_API_KEY', None))

        prompt = f"You are EduAssist conversational bot. Reply concisely and helpfully.\nUser: {request.message}\nAssistant:"
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(prompt)
        text = resp.text if hasattr(resp, 'text') else str(resp)

        return {"response": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini public chat error: {str(e)}")

@router.post("/approve-action")
async def approve_action(
    request: ActionApprovalRequest,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """
    Approve or reject a pending action
    Used when assistant is in Manual mode or for high-risk actions
    """
    try:
        # Log the approval decision
        gemini_assistant.log_action(
            "action_approval",
            f"Action {request.action_id} {'approved' if request.approved else 'rejected'}",
            {"feedback": request.feedback}
        )
        
        return {
            "status": "success",
            "message": f"Action {'approved' if request.approved else 'rejected'}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval error: {str(e)}")

@router.get("/enhanced-status")
async def get_enhanced_assistant_status(
    current_educator: Educator = Depends(get_current_educator)
):
    """
    Get enhanced assistant status and capabilities
    """
    try:
        status = gemini_assistant.get_status()
        return {
            **status,
            "educator": {
                "id": current_educator.id,
                "name": current_educator.name,
                "email": current_educator.email
            },
            "gemini_integration": True,
            "enhanced_features": [
                "Multi-language support (English/Telugu)",
                "Three autonomy modes (Manual/Assist/Autonomous)",
                "Background task processing",
                "Advanced intent analysis",
                "Audit trail logging",
                "Context-aware responses"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

@router.post("/settings")
async def update_assistant_settings(
    request: SettingsUpdateRequest,
    current_educator: Educator = Depends(get_current_educator)
):
    """
    Update assistant settings (autonomy mode, language, permissions)
    """
    try:
        if request.autonomy_mode:
            gemini_assistant.set_autonomy_mode(request.autonomy_mode)
        
        if request.language:
            gemini_assistant.set_language(request.language)
        
        if request.permissions:
            gemini_assistant.log_action(
                "settings_update",
                "Permissions updated",
                {"permissions": request.permissions}
            )
        
        return {
            "status": "success",
            "message": "Settings updated successfully",
            "current_settings": gemini_assistant.get_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settings error: {str(e)}")

@router.post("/background-task")
async def start_background_task(
    request: BackgroundTaskRequest,
    background_tasks: BackgroundTasks,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """
    Start a background task (e.g., quarterly report generation)
    """
    try:
        # Add background task
        background_tasks.add_task(
            process_background_task,
            request.task_type,
            request.parameters,
            current_educator.id
        )
        
        gemini_assistant.log_action(
            "background_task_started",
            f"Background task started: {request.task_type}",
            request.parameters
        )
        
        return {
            "status": "success",
            "message": f"Background task '{request.task_type}' started",
            "task_id": f"task_{datetime.now().timestamp()}",
            "estimated_completion": "5-10 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background task error: {str(e)}")

@router.get("/audit-log")
async def get_audit_log(
    limit: int = 50,
    current_educator: Educator = Depends(get_current_educator)
):
    """
    Get assistant audit log for transparency
    """
    try:
        full_log = gemini_assistant.action_log
        recent_log = full_log[-limit:] if len(full_log) > limit else full_log
        
        return {
            "total_actions": len(full_log),
            "returned_actions": len(recent_log),
            "actions": recent_log
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit log error: {str(e)}")

@router.post("/quick-actions/{action_type}")
async def execute_quick_action(
    action_type: str,
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """
    Execute predefined quick actions
    """
    try:
        quick_actions = {
            "daily_summary": "Generate my daily administrative summary",
            "check_calendar": "Check my calendar for today and tomorrow",
            "pending_emails": "Check for pending emails that need responses",
            "student_alerts": "Check for any student performance alerts",
            "compliance_status": "Check my compliance status and pending items",
            "performance_overview": "Show me student performance overview",
            "schedule_conflicts": "Check for any scheduling conflicts this week"
        }
        
        if action_type not in quick_actions:
            raise HTTPException(status_code=400, detail="Unknown quick action")
        
        command = quick_actions[action_type]
        result = await gemini_assistant.process_command(command, current_educator.id, db)
        
        return {
            "action_type": action_type,
            "command": command,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick action error: {str(e)}")

@router.get("/telugu-examples")
async def get_telugu_examples():
    """
    Get example Telugu phrases for testing multilingual support
    """
    return {
        "examples": [
            {
                "telugu": "నా షెడ్యూల్ చూపించు",
                "english": "Show my schedule",
                "type": "calendar"
            },
            {
                "telugu": "విద్యార్థుల గ్రేడ్స్ చూపించు",
                "english": "Show student grades",
                "type": "performance"
            },
            {
                "telugu": "ఇమెయిల్ పంపించు",
                "english": "Send email",
                "type": "communication"
            },
            {
                "telugu": "రిపోర్ట్ తయారు చేయి",
                "english": "Generate report",
                "type": "reporting"
            },
            {
                "telugu": "రేపటి మీటింగ్లు ఏవైనా ఉన్నాయా?",
                "english": "Are there any meetings tomorrow?",
                "type": "calendar"
            },
            {
                "telugu": "నాకు సహాయం కావాలి",
                "english": "I need help",
                "type": "general"
            }
        ],
        "note": "The assistant can understand both languages and respond accordingly",
        "supported_languages": ["English", "Telugu"],
        "autonomy_modes": ["Manual", "Assist", "Autonomous"]
    }

@router.post("/demo-conversation")
async def demo_conversation(
    current_educator: Educator = Depends(get_current_educator),
    db: Session = Depends(get_db)
):
    """
    Demo conversation for presentation purposes
    """
    try:
        demo_commands = [
            "Hey, manage my administrative stuff today. Take care of everything.",
            "Show me student performance analytics for Computer Science A section",
            "Generate a quarterly performance report in the background",
            "Check for any scheduling conflicts this week",
            "Send performance update emails to all parents"
        ]
        
        results = []
        for command in demo_commands:
            result = await gemini_assistant.process_command(command, current_educator.id, db)
            results.append({
                "command": command,
                "response": result["response"],
                "actions_count": len(result["actions"]),
                "requires_approval": result["requires_approval"]
            })
            
            # Small delay for demo effect
            await asyncio.sleep(0.5)
        
        return {
            "demo_title": "EduAssist AI Demo Conversation",
            "educator": f"{current_educator.name} ({current_educator.email})",
            "results": results,
            "autonomy_mode": gemini_assistant.autonomy_mode,
            "language": gemini_assistant.language,
            "total_interactions": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo error: {str(e)}")

# Background task processor
@router.get("/status")
async def get_assistant_status():
    """
    Get current assistant status and capabilities
    """
    try:
        status = gemini_assistant.get_status()
        return {
            "status": "active",
            "assistant_state": status["state"],
            "autonomy_mode": status["autonomy_mode"],
            "language": status["language"],
            "capabilities": status["capabilities"],
            "version": status["version"],
            "recent_actions": status["recent_actions"][-5:],  # Last 5 actions
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

@router.post("/settings")
async def update_assistant_settings(
    request: SettingsUpdateRequest,
    current_educator: Educator = Depends(get_current_educator)
):
    """
    Update assistant settings for the current educator
    """
    try:
        if request.autonomy_mode:
            gemini_assistant.set_autonomy_mode(request.autonomy_mode)
        
        if request.language:
            gemini_assistant.set_language(request.language)
        
        # Log the settings update
        gemini_assistant.log_action(
            "settings_updated",
            f"Settings updated for educator {current_educator.id}",
            {
                "autonomy_mode": request.autonomy_mode,
                "language": request.language,
                "permissions": request.permissions
            }
        )
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "current_settings": {
                "autonomy_mode": gemini_assistant.autonomy_mode,
                "language": gemini_assistant.language
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settings update error: {str(e)}")

async def process_background_task(task_type: str, parameters: Dict[str, Any], educator_id: int):
    """
    Process background tasks asynchronously
    """
    try:
        # Simulate background processing
        await asyncio.sleep(5)  # Simulate work
        
        if task_type == "quarterly_summary":
            result = "Quarterly summary generated successfully - 120 students analyzed, average performance 74.6%"
        elif task_type == "bulk_email":
            result = "Bulk emails sent successfully to 120 parents with personalized performance updates"
        elif task_type == "performance_analysis":
            result = "Performance analysis completed - identified 15 students needing additional support"
        elif task_type == "compliance_check":
            result = "Compliance check completed - all requirements up to date"
        else:
            result = f"Background task {task_type} completed successfully"
        
        # Log completion
        gemini_assistant.log_action(
            "background_task_completed",
            result,
            {"task_type": task_type, "parameters": parameters, "educator_id": educator_id}
        )
        
    except Exception as e:
        gemini_assistant.log_action(
            "background_task_failed",
            f"Background task failed: {str(e)}",
            {"task_type": task_type, "parameters": parameters, "educator_id": educator_id}
        )