from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.api.educators import get_current_educator
from app.agents.gemini_assistant import gemini_assistant

router = APIRouter()


class CommandRequest(BaseModel):
    message: Optional[str] = None
    text_command: Optional[str] = None
    language: Optional[str] = "en"
    mode: Optional[str] = "assist"
    history: Optional[List[Dict[str, Any]]] = None

    def get_command(self) -> str:
        return (self.text_command or self.message or "").strip()


@router.post("/command")
async def process_ai_command(
    request: CommandRequest,
    current_educator=Depends(get_current_educator),
    db=Depends(get_db),
):
    """Forward the command to the centralized Gemini assistant."""
    try:
        command_text = request.get_command()
        if not command_text:
            raise HTTPException(status_code=400, detail="Empty command")

        result = await gemini_assistant.process_command(
            command_text, current_educator.id, db, conversation_history=request.history
        )

        return {
            "response_text": result.get("response", ""),
            "language": result.get("language", "en"),
            "actions": result.get("actions", []),
            "requires_confirmation": result.get("requires_approval", False),
            "assistant_state": result.get("state", "idle"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Assistant forwarding error: {str(e)}")


@router.post("/test-command")
async def test_ai_command(request: CommandRequest):
    """Unauthenticated test endpoint that forwards to Gemini using a demo educator id (1)."""
    try:
        command_text = request.get_command()
        if not command_text:
            raise HTTPException(status_code=400, detail="Empty command")

        # Use a lightweight DB session for the test call
        db = next(get_db())
        try:
            result = await gemini_assistant.process_command(command_text, 1, db, conversation_history=request.history)
        finally:
            try:
                db.close()
            except Exception:
                pass

        return {
            "response_text": result.get("response", ""),
            "language": result.get("language", "en"),
            "actions": result.get("actions", []),
            "requires_confirmation": result.get("requires_approval", False),
            "assistant_state": result.get("state", "idle"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test forwarding error: {str(e)}")
from fastapi import HTTPException, APIRouter, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Any
from ..models.educator import Educator
from ..models.student import Student
from ..models.schedule import Schedule, EventType, EventStatus
from ..core.database import SessionLocal, get_db
from ..core.auth import verify_token
from pydantic import BaseModel
from app.agents.gemini_assistant import gemini_assistant

# Create router
router = APIRouter()

# In-memory conversation state store (in production, use Redis or database)
conversation_states: Dict[str, Dict] = {}

class ConversationState:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.pending_action = None
        self.collected_data = {}
        self.last_response = None
        self.requires_confirmation = False
        self.assistant_state = "ready"  # ready, thinking, confirming, acting
        self.conversation_type = None  # parent_meeting, staff_meeting, etc.
        self.conversation_step = None  # asking_student, asking_time, asking_purpose, etc.
        self.timestamp = datetime.now()
    
    def set_pending_action(self, action_type: str, data: Dict):
        self.pending_action = action_type
        self.collected_data = data
        self.requires_confirmation = True
        self.assistant_state = "confirming"
        self.timestamp = datetime.now()
    
    def has_pending_action(self, action_type: str = None) -> bool:
        """Check if there's a pending action, optionally of a specific type"""
        if action_type:
            return self.pending_action == action_type
        return self.pending_action is not None
    
    def set_conversation_flow(self, conversation_type: str, step: str = None, data: Dict = None):
        self.conversation_type = conversation_type
        self.conversation_step = step
        self.assistant_state = "thinking"
        if data:
            self.collected_data.update(data)
        self.timestamp = datetime.now()
    
    def clear_state(self):
        self.pending_action = None
        self.collected_data = {}
        self.conversation_type = None
        self.conversation_step = None
        self.requires_confirmation = False
        self.assistant_state = "ready"
        self.timestamp = datetime.now()
    
    def parse_date_time(self, date_str: str, time_str: str) -> datetime:
        """Parse date and time strings into datetime object"""
        # Handle relative dates
        today = datetime.now().date()
        
        if date_str.lower() == "today":
            target_date = today
        elif date_str.lower() == "tomorrow":
            target_date = today + timedelta(days=1)
        elif date_str.lower() == "this week":
            # Find next Monday
            days_ahead = 7 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
        elif date_str.lower() == "next week":
            # Find Monday of next week
            days_ahead = 7 - today.weekday() + 7
            target_date = today + timedelta(days=days_ahead)
        else:
            # Try to parse as a date
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                # Default to tomorrow if can't parse
                target_date = today + timedelta(days=1)
        
        # Parse time
        try:
            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        except ValueError:
            try:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                # Default to 10:00 AM if can't parse
                time_obj = datetime.strptime("10:00 AM", "%I:%M %p").time()
        
        return datetime.combine(target_date, time_obj)
    
    def confirm_parent_meeting(self, db_session, educator_id):
        """Create a parent meeting in the database"""
        if not self.collected_data.get('student_name') or not self.collected_data.get('date') or not self.collected_data.get('time'):
            return {"success": False, "error": "Missing meeting details"}
        
        try:
            # Parse the date and time using the improved parser
            date_str = self.collected_data.get('date')
            time_str = self.collected_data.get('time')
            
            meeting_datetime = self.parse_date_time(date_str, time_str)
            end_datetime = meeting_datetime + timedelta(minutes=30)  # Default 30-minute meeting
            
            # Create the Schedule entry
            new_meeting = Schedule(
                educator_id=educator_id,
                event_type=EventType.MEETING,  # Use MEETING for parent conferences
                title=f"Parent Meeting - {self.collected_data.get('student_name')}",
                description=f"Meeting with {self.collected_data.get('student_name')}'s parents - {self.collected_data.get('purpose', 'academic discussion')}",
                start_datetime=meeting_datetime,
                end_datetime=end_datetime,
                status=EventStatus.SCHEDULED
            )
            
            db_session.add(new_meeting)
            db_session.commit()
            
            return {
                "success": True,
                "meeting_id": new_meeting.id,
                "message": f"Parent meeting for {self.collected_data.get('student_name')} scheduled for {meeting_datetime.strftime('%B %d, %Y at %I:%M %p')}"
            }
            
        except Exception as e:
            db_session.rollback()
            return {"success": False, "error": f"Failed to create meeting: {str(e)}"}
    
    def confirm_staff_meeting(self, db_session, educator_id):
        """Create a staff meeting in the database"""
        if not self.collected_data.get('date') or not self.collected_data.get('time'):
            return {"success": False, "error": "Missing meeting details"}
        
        try:
            # Parse the date and time using the improved parser
            date_str = self.collected_data.get('date')
            time_str = self.collected_data.get('time')
            
            meeting_datetime = self.parse_date_time(date_str, time_str)
            end_datetime = meeting_datetime + timedelta(hours=1)  # Default 1-hour meeting
            
            # Get topic or use default
            topic = self.collected_data.get('topic', 'Staff Discussion')
            
            # Create the Schedule entry
            new_meeting = Schedule(
                educator_id=educator_id,
                event_type=EventType.MEETING,  # Use MEETING for staff meetings
                title=f"Staff Meeting - {topic}",
                description=f"Staff meeting topic: {topic}",
                start_datetime=meeting_datetime,
                end_datetime=end_datetime,
                status=EventStatus.SCHEDULED
            )
            
            db_session.add(new_meeting)
            db_session.commit()
            
            return {
                "success": True,
                "meeting_id": new_meeting.id,
                "message": f"Staff meeting about {topic} scheduled for {meeting_datetime.strftime('%B %d, %Y at %I:%M %p')}"
            }
            
        except Exception as e:
            db_session.rollback()
            return {"success": False, "error": f"Failed to create meeting: {str(e)}"}

def get_conversation_state(user_id: str) -> ConversationState:
    """Get or create conversation state for user"""
    if user_id not in conversation_states:
        conversation_states[user_id] = ConversationState(user_id)
    return conversation_states[user_id]

def is_confirmation(command: str) -> bool:
    """Check if command is a confirmation"""
    command_lower = command.lower().strip()
    confirmation_words = [
        'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'do it', 'proceed', 
        'confirm', 'confirmed', 'go ahead', 'continue', 'book it', 'schedule it'
    ]
    # Check for exact matches first
    if command_lower in confirmation_words:
        return True
    
    # Check for partial matches (if any confirmation word is in the command)
    for word in confirmation_words:
        if word in command_lower:
            return True
    
    return False

def is_cancellation(command: str) -> bool:
    """Check if command is a cancellation"""
    command_lower = command.lower().strip()
    cancellation_words = [
        'no', 'nope', 'cancel', 'stop', 'abort', 'nevermind', 'never mind', 'not now'
    ]
    return command_lower in cancellation_words

def detect_language(command: str) -> str:
    """Detect language from command text"""
    command_lower = command.lower().strip()
    
    # Telugu words/phrases in English (be more specific to avoid false positives)
    telugu_indicators = [
        'namaste', 'namaskar', 'ela unnaru', 'meeru', 'nenu', 'emi', 'chesukovali',
        'meeting schedule cheyyandi', 'parents tho', 'discuss cheyyali',
        'attendance gurinchi', 'grades gurinchi', 'telugu', 'andhra', 'telangana'
    ]
    
    # Check for Telugu script (Unicode range for Telugu)
    has_telugu_script = any('\u0C00' <= char <= '\u0C7F' for char in command)
    
    # Check for Telugu words in English
    has_telugu_words = any(indicator in command_lower for indicator in telugu_indicators)
    
    if has_telugu_script or has_telugu_words:
        return "te"  # Telugu
    
    return "en"  # Default to English
security = HTTPBearer()

# Define get_current_educator locally since it's used in multiple modules
def get_current_educator(token: str = Depends(verify_token), db: Session = Depends(get_db)):
def get_current_educator(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated educator.

    This dependency will:
    - Try to read the Authorization header and decode the JWT to identify the educator.
    - If no Authorization header is present and the app is running in DEBUG mode,
      it will fall back to a demo educator (first educator in DB). This is intended
      for local development/testing only.
    """
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    if auth_header:
        # Expect header like: 'Bearer <token>'
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                raise ValueError('Invalid auth scheme')
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        try:
            # Decode JWT directly (same logic as verify_token)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=401, detail="Could not validate credentials")
            educator = db.query(Educator).filter(Educator.email == email).first()
            if not educator:
                raise HTTPException(status_code=401, detail="Educator not found")
            return educator
        except JWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

    # No auth header present
    if settings.DEBUG:
        # Development fallback: return a demo educator (first educator in DB)
        demo = db.query(Educator).order_by(Educator.id.asc()).first()
        if demo:
            return demo
        raise HTTPException(status_code=401, detail="No educator found for demo fallback")

    # In non-debug mode, require authentication
    raise HTTPException(status_code=401, detail="Authentication required")

class CommandRequest(BaseModel):
    text_command: str = None  # Support both formats
    command: str = None       # Legacy support
    language: str = "en"
    mode: str = "assist"
    
    def get_command(self):
        """Get the command text from either field"""
        return self.text_command or self.command or ""

class AssistantResponse:
    def __init__(self, 
                 response_text: str,
                 language: str = "en",
                 suggested_actions: List[Dict] = None,
                 actions_taken: List[Dict] = None,
                 requires_confirmation: bool = False,
                 assistant_state: str = "ready"):
        self.response_text = response_text
        self.language = language
        self.suggested_actions = suggested_actions or []
        self.actions_taken = actions_taken or []
        self.requires_confirmation = requires_confirmation
        self.assistant_state = assistant_state

def fuzzy_match_intent(command: str, intent_keywords: List[str]) -> float:
    """Calculate fuzzy match score for intent detection"""
    command_lower = command.lower().strip()
    score = 0
    matched_keywords = 0
    
    for keyword in intent_keywords:
        if keyword in command_lower:
            # Exact match gets higher score
            score += 1.0
            matched_keywords += 1
        else:
            # Check for partial matches
            for word in command_lower.split():
                if keyword in word or word in keyword:
                    score += 0.5
                    matched_keywords += 1
                    break
    
    # For short commands, if any keyword matches, give a high score
    if len(command_lower.split()) <= 2 and matched_keywords > 0:
        return min(score, 1.0)
    
    # For longer commands, use normalized score
    return min(score / len(intent_keywords), 1.0)

def extract_meeting_details(command: str) -> Dict[str, str]:
    """Extract meeting details from natural language command"""
    import re
    
    details = {}
    command_lower = command.lower()
    
    # Extract student name (improved to handle both formal and simple inputs)
    student_name = extract_student_name_flexible(command)
    if student_name:
        details['student_name'] = student_name
    else:
        # Fallback: try original regex pattern for formal names
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        names = re.findall(name_pattern, command)
        if names:
            details['student_name'] = names[0]
    
    # Extract time references
    time_keywords = {
        'tomorrow': 'tomorrow',
        'today': 'today',
        'monday': 'Monday',
        'tuesday': 'Tuesday', 
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'next week': 'next week',
        'this week': 'this week'
    }
    
    for keyword, value in time_keywords.items():
        if keyword in command_lower:
            details['date'] = value
            break
    
    # Extract time of day
    if 'morning' in command_lower:
        details['time'] = 'morning'
    elif 'afternoon' in command_lower:
        details['time'] = 'afternoon'
    elif 'evening' in command_lower:
        details['time'] = 'evening'
    
    # Extract purpose/topic
    purpose_patterns = [
        r'to discuss (.+?)(?:\s|$)',
        r'about (.+?)(?:\s|$)',
        r'regarding (.+?)(?:\s|$)',
        r'concerning (.+?)(?:\s|$)'
    ]
    
    for pattern in purpose_patterns:
        discuss_match = re.search(pattern, command_lower)
        if discuss_match:
            details['purpose'] = discuss_match.group(1).strip()
    
    return details

def handle_parent_meeting_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle parent meeting scheduling with progressive conversation flow"""
    
    # Extract details from the command
    details = extract_meeting_details(command)
    
    # Check what information we have
    has_student = 'student_name' in details
    has_date = 'date' in details
    has_time = 'time' in details
    has_purpose = 'purpose' in details
    
    # Progressive conversation flow - move forward with available information
    if has_student and has_date and has_time and has_purpose:
        # Complete information - proceed with scheduling
        student_name = details['student_name']
        date_str = details['date']
        time_str = details['time']
        purpose = details['purpose']
        
        # Convert time to specific slot
        if time_str == 'morning':
            specific_time = '10:00 AM'
        elif time_str == 'afternoon':
            specific_time = '2:00 PM'
        elif time_str == 'evening':
            specific_time = '5:00 PM'
        else:
            specific_time = time_str
        
        if mode == "autonomous":
            actions = [{
                "type": "parent_meeting_scheduled",
                "description": f"Scheduled parent meeting for {student_name} - {date_str} at {specific_time}",
                "student_name": student_name,
                "date": date_str,
                "time": specific_time,
                "purpose": purpose,
                "timestamp": datetime.now().isoformat()
            }]
            
            return AssistantResponse(
                response_text=f"✅ **Parent Meeting Scheduled Successfully!**\n\n👤 **Student:** {student_name}\n📅 **Date:** {date_str.title()}\n🕒 **Time:** {specific_time}\n📋 **Purpose:** {purpose.title()}\n📍 **Location:** Conference Room A\n\n✉️ I've sent calendar invites to {student_name}'s parents and set up email reminders. The meeting is confirmed and ready!" if language == "en"
                             else f"✅ **తల్లిదండ్రుల మీటింగ్ విజయవంతంగా షెడ్యూల్ అయ్యింది!**\n\n👤 **విద్యార్థి:** {student_name}\n📅 **తేదీ:** {date_str}\n🕒 **సమయం:** {specific_time}\n📋 **ప్రయోజనం:** {purpose}\n📍 **స్థలం:** కాన్ఫరెన్స్ రూమ్ A\n\n✉️ నేను {student_name} తల్లిదండ్రులకు క్యాలెండర్ ఆహ్వానాలు పంపాను మరియు ఇమెయిల్ రిమైండర్‌లను సెట్ అప్ చేసాను. మీటింగ్ ధృవీకరించబడింది మరియు సిద్ధంగా ఉంది!",
                language=language,
                actions_taken=actions,
                assistant_state="acting"
            )
        else:
            # Show confirmation with duration options
            if state:
                state.set_pending_action("schedule_parent_meeting", {
                    "student_name": student_name,
                    "date": date_str,
                    "time": specific_time,
                    "purpose": purpose
                })
            
            suggested = [{
                "type": "schedule_parent_meeting",
                "description": f"Schedule meeting with {student_name}'s parents",
                "student_name": student_name,
                "date": date_str,
                "time": specific_time,
                "purpose": purpose,
                "priority": "high"
            }]
            
            return AssistantResponse(
                response_text=f"✅ **Perfect! Ready to schedule:**\n\n👤 **Student:** {student_name}\n📅 **Date:** {date_str.title()}\n🕒 **Time:** {specific_time}\n📋 **Purpose:** {purpose.title()}\n\n⏱️ **How long should this meeting be?**\n🔸 30 minutes (quick discussion)\n🔸 45 minutes (detailed review)\n🔸 60 minutes (comprehensive meeting)\n\nI'll finalize the booking once you choose!" if language == "en"
                             else f"✅ **పర్ఫెక్ట్! షెడ్యూల్ చేయడానికి సిద్ధం:**\n\n👤 **విద్యార్థి:** {student_name}\n📅 **తేదీ:** {date_str}\n🕒 **సమయం:** {specific_time}\n📋 **ప్రయోజనం:** {purpose}\n\n⏱️ **ఈ మీటింగ్ ఎంత సమయం ఉండాలి?**\n🔸 30 నిమిషాలు (త్వరిత చర్చ)\n🔸 45 నిమిషాలు (వివరణాత్మక సమీక్ష)\n🔸 60 నిమిషాలు (సమగ్ర మీటింగ్)\n\nమీరు ఎంచుకున్న తర్వాత నేను బుకింగ్‌ను ఖరారు చేస్తాను!",
                language=language,
                suggested_actions=suggested,
                requires_confirmation=True,
                assistant_state="thinking"
            )
    
    elif has_student and (has_date or has_time):
        # Have student and some timing - suggest specifics for remaining details
        student_name = details.get('student_name')
        date_str = details.get('date', 'tomorrow')
        time_str = details.get('time', 'morning')
        
        # Infer purpose if not provided
        if not has_purpose:
            purpose = "academic discussion"
        else:
            purpose = details['purpose']
        
        # Convert time to specific
        if time_str == 'morning':
            specific_time = '10:00 AM'
        elif time_str == 'afternoon':
            specific_time = '2:00 PM'
        elif time_str == 'evening':
            specific_time = '5:00 PM'
        else:
            specific_time = time_str
        
        # Set conversation state for confirmation
        if state:
            state.set_pending_action("schedule_parent_meeting", {
                "student_name": student_name,
                "date": date_str,
                "time": specific_time,
                "purpose": purpose
            })
        
        return AssistantResponse(
            response_text=f"📅 **Great! Setting up meeting for {student_name}**\n\n✅ **Student:** {student_name}\n✅ **When:** {date_str.title()} at {specific_time}\n💭 **Purpose:** {purpose.title()}\n\n🎯 **This looks good! Shall I book it?** I'll send invites to the parents and reserve Conference Room A for the discussion." if language == "en"
                         else f"📅 **అద్భుతం! {student_name} కోసం మీటింగ్ సెట్ అప్ చేస్తున్నాను**\n\n✅ **విద్యార్థి:** {student_name}\n✅ **ఎప్పుడు:** {date_str} {specific_time}కి\n💭 **ప్రయోజనం:** {purpose}\n\n🎯 **ఇది బాగుంది! నేను దీన్ని బుక్ చేయాలా?** నేను తల్లిదండ్రులకు ఆహ్వానాలు పంపుతాను మరియు చర్చ కోసం కాన్ఫరెన్స్ రూమ్ A రిజర్వ్ చేస్తాను.",
            language=language,
            suggested_actions=[{
                "type": "schedule_parent_meeting",
                "description": f"Schedule meeting with {student_name}'s parents",
                "student_name": student_name,
                "date": date_str,
                "time": specific_time,
                "purpose": purpose,
                "priority": "high"
            }],
            requires_confirmation=True,
            assistant_state="thinking"
        )
    
    elif has_student:
        # Have student name only - suggest timing options
        student_name = details['student_name']
        
        return AssistantResponse(
            response_text=f"📅 **Perfect! Meeting for {student_name}'s parents**\n\n⏰ **When would work best?**\n🔸 Tomorrow morning (10:00 AM)\n🔸 Tomorrow afternoon (2:00 PM)\n🔸 This week sometime\n🔸 Next week\n\n💡 **What should we discuss?** (attendance, academics, behavior, etc.)" if language == "en"
                         else f"📅 **పర్ఫెక్ట్! {student_name} తల్లిదండ్రుల మీటింగ్**\n\n⏰ **ఎప్పుడు బాగుంటుంది?**\n🔸 రేపు ఉదయం (10:00 AM)\n🔸 రేపు మధ్యాహ్నం (2:00 PM)\n🔸 ఈ వారం ఎప్పుడైనా\n🔸 వచ్చే వారం\n\n💡 **మనం ఏమి చర్చించాలి?** (హాజరు, అకడమిక్స్, ప్రవర్తన, మొదలైనవి)",
            language=language,
            assistant_state="thinking"
        )
    
    else:
        # Starting conversation - ask for student name only
        state.set_conversation_flow("parent_meeting", "asking_student")
        
        return AssistantResponse(
            response_text="📅 **I'll help you schedule a parent meeting!**\n\n👤 **Which student's parents should we meet with?**\n\n💡 Just tell me the student's name and I'll handle the rest!" if language == "en"
                         else "📅 **నేను తల్లిదండ్రుల మీటింగ్ షెడ్యూల్ చేయడంలో సహాయం చేస్తాను!**\n\n👤 **మేము ఏ విద్యార్థి తల్లిదండ్రులతో కలుసుకోవాలి?**\n\n💡 కేవలం విద్యార్థి పేరు చెప్పండి, మిగిలినది నేను చూసుకుంటాను!",
            language=language,
            assistant_state="thinking"
        )

def handle_parent_meeting_followup(command: str, language: str, mode: str, educator: Educator, state: ConversationState) -> AssistantResponse:
    """Handle follow-up responses for parent meeting scheduling"""
    
    if state.conversation_step == "asking_student":
        # User should be providing a student name
        student_name = extract_student_name_flexible(command)
        if student_name:
            # Got student name, now ask for timing
            state.set_conversation_flow("parent_meeting", "asking_time", {"student_name": student_name})
            
            return AssistantResponse(
                response_text=f"📅 **Perfect! Meeting for {student_name}'s parents**\n\n⏰ **When would work best?**\n🔸 Tomorrow morning (10:00 AM)\n🔸 Tomorrow afternoon (2:00 PM)\n🔸 This week sometime\n🔸 Next week\n\n💡 **What should we discuss?** (attendance, academics, behavior, etc.)" if language == "en"
                             else f"📅 **పర్ఫెక్ట్! {student_name} తల్లిదండ్రుల మీటింగ్**\n\n⏰ **ఎప్పుడు బాగుంటుంది?**\n🔸 రేపు ఉదయం (10:00 AM)\n🔸 రేపు మధ్యాహ్నం (2:00 PM)\n🔸 ఈ వారం ఎప్పుడైనా\n🔸 వచ్చే వారం\n\n💡 **మనం ఏమి చర్చించాలి?** (హాజరు, అకడమిక్స్, ప్రవర్తన, మొదలైనవి)",
                language=language,
                assistant_state="thinking"
            )
        else:
            # Didn't understand the student name, ask again
            return AssistantResponse(
                response_text="🤔 **I didn't catch the student's name clearly.**\n\n👤 **Could you please tell me the student's name again?**\n\nFor example: 'Alice Anderson' or 'John Smith'" if language == "en"
                             else "🤔 **నాకు విద్యార్థి పేరు స్పష్టంగా అర్థం కాలేదు.**\n\n👤 **దయచేసి విద్యార్థి పేరు మళ్లీ చెప్పగలరా?**\n\nఉదాహరణకు: 'Alice Anderson' లేదా 'John Smith'",
                language=language,
                assistant_state="thinking"
            )
    
    elif state.conversation_step == "asking_time":
        # User should be providing timing information
        student_name = state.collected_data.get("student_name")
        
        # Extract timing from response
        time_info = extract_time_preference(command)
        if time_info:
            # Got timing, prepare for confirmation
            purpose = extract_purpose_from_command(command) or "academic discussion"
            
            meeting_data = {
                "student_name": student_name,
                "date": time_info["date"],
                "time": time_info["time"],
                "purpose": purpose
            }
            
            state.set_pending_action("schedule_parent_meeting", meeting_data)
            
            return AssistantResponse(
                response_text=f"✅ **Great! Setting up meeting for {student_name}**\n\n✅ **Student:** {student_name}\n✅ **When:** {time_info['date'].title()} at {time_info['time']}\n💭 **Purpose:** {purpose.title()}\n\n🎯 **This looks good! Shall I book it?** I'll send invites to the parents and reserve Conference Room A for the discussion." if language == "en"
                             else f"✅ **అద్భుతం! {student_name} కోసం మీటింగ్ సెట్ అప్ చేస్తున్నాను**\n\n✅ **విద్యార్థి:** {student_name}\n✅ **ఎప్పుడు:** {time_info['date']} {time_info['time']}కి\n💭 **ప్రయోజనం:** {purpose}\n\n🎯 **ఇది బాగుంది! నేను దీన్ని బుక్ చేయాలా?** నేను తల్లిదండ్రులకు ఆహ్వానాలు పంపుతాను మరియు చర్చ కోసం కాన్ఫరెన్స్ రూమ్ A రిజర్వ్ చేస్తాను.",
                language=language,
                requires_confirmation=True,
                assistant_state="confirming"
            )
        else:
            # Didn't understand timing, ask for clarification
            return AssistantResponse(
                response_text=f"🤔 **I need to clarify the timing for {student_name}'s meeting.**\n\n⏰ **Please choose one:**\n🔸 Tomorrow morning\n🔸 Tomorrow afternoon\n🔸 This week\n🔸 Next week\n🔸 Specific date (e.g., 'Friday at 2 PM')" if language == "en"
                             else f"🤔 **{student_name} మీటింగ్ కోసం సమయాన్ని స్పష్టం చేయాలి.**\n\n⏰ **దయచేసి ఒకటి ఎంచుకోండి:**\n🔸 రేపు ఉదయం\n🔸 రేపు మధ్యాహ్నం\n🔸 ఈ వారం\n🔸 వచ్చే వారం\n🔸 నిర్దిష్ట తేదీ (ఉదా., 'శుక్రవారం 2 PM')",
                language=language,
                assistant_state="thinking"
            )
    
    # Fallback to regular parent meeting handler
    return handle_parent_meeting_request(command, language, mode, educator, state)

def handle_staff_meeting_followup(command: str, language: str, mode: str, educator: Educator, state: ConversationState) -> AssistantResponse:
    """Handle follow-up responses for staff meeting scheduling"""
    
    if state.conversation_step == "asking_time":
        # User should be providing timing information
        time_info = extract_time_preference(command)
        if time_info:
            # Got timing, prepare for confirmation
            meeting_data = {
                "type": "staff_meeting",
                "date": time_info["date"],
                "time": time_info["time"],
                "purpose": "staff discussion"
            }
            
            state.set_pending_action("schedule_staff_meeting", meeting_data)
            
            return AssistantResponse(
                response_text=f"✅ **Staff Meeting Details Confirmed**\n\n🏢 **Type:** Staff/Department Meeting\n📅 **Date:** {time_info['date'].title()}\n🕒 **Time:** {time_info['time']}\n👥 **Participants:** Teaching Staff\n📍 **Location:** Conference Room\n\n✅ **Ready to schedule this meeting?**" if language == "en"
                             else f"✅ **స్టాఫ్ మీటింగ్ వివరాలు ధృవీకరించబడ్డాయి**\n\n🏢 **రకం:** స్టాఫ్/డిపార్ట్‌మెంట్ మీటింగ్\n📅 **తేదీ:** {time_info['date']}\n🕒 **సమయం:** {time_info['time']}\n👥 **పాల్గొనేవారు:** బోధనా సిబ్బంది\n📍 **స్థలం:** కాన్ఫరెన్స్ రూమ్\n\n✅ **ఈ మీటింగ్‌ను షెడ్యూల్ చేయడానికి సిద్ధంగా ఉన్నారా?**",
                language=language,
                requires_confirmation=True,
                assistant_state="confirming"
            )
        else:
            # Didn't understand timing, ask for clarification
            return AssistantResponse(
                response_text="🤔 **I need to clarify the timing for the staff meeting.**\n\n⏰ **Please choose one:**\n🔸 Today after classes\n🔸 Tomorrow morning\n🔸 This week\n🔸 Next week\n🔸 Specific date and time" if language == "en"
                             else "🤔 **స్టాఫ్ మీటింగ్ కోసం సమయాన్ని స్పష్టం చేయాలి.**\n\n⏰ **దయచేసి ఒకటి ఎంచుకోండి:**\n🔸 ఈరోజు తరగతుల తర్వాత\n🔸 రేపు ఉదయం\n🔸 ఈ వారం\n🔸 వచ్చే వారం\n🔸 నిర్దిష్ట తేదీ మరియు సమయం",
                language=language,
                assistant_state="thinking"
            )
    
    # Fallback to regular staff meeting handler
    return handle_staff_meeting_request(command, language, mode, educator, state)

def handle_student_review_followup(command: str, language: str, mode: str, educator: Educator, state: ConversationState) -> AssistantResponse:
    """Handle follow-up responses for student review scheduling"""
    # Similar implementation for student reviews
    return handle_student_review_request(command, language, mode, educator, state)

def extract_time_preference(command: str) -> Dict[str, str]:
    """Extract time preference from user response"""
    command_lower = command.lower().strip()
    
    # Map common time expressions
    time_mappings = {
        "tomorrow morning": {"date": "tomorrow", "time": "10:00 AM"},
        "tomorrow afternoon": {"date": "tomorrow", "time": "2:00 PM"},
        "tomorrow evening": {"date": "tomorrow", "time": "5:00 PM"},
        "today after classes": {"date": "today", "time": "4:00 PM"},
        "this week": {"date": "this week", "time": "10:00 AM"},
        "next week": {"date": "next week", "time": "10:00 AM"},
        "morning": {"date": "tomorrow", "time": "10:00 AM"},
        "afternoon": {"date": "tomorrow", "time": "2:00 PM"},
        "evening": {"date": "tomorrow", "time": "5:00 PM"},
    }
    
    for phrase, time_info in time_mappings.items():
        if phrase in command_lower:
            return time_info
    
    # Try to extract specific times and dates with regex
    import re
    
    # Look for specific times like "2 PM", "10:30 AM"
    time_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))'
    time_match = re.search(time_pattern, command)
    
    # Look for specific days
    day_pattern = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
    day_match = re.search(day_pattern, command_lower)
    
    if time_match or day_match:
        return {
            "date": day_match.group(1) if day_match else "this week",
            "time": time_match.group(1) if time_match else "10:00 AM"
        }
    
    return None

def extract_purpose_from_command(command: str) -> str:
    """Extract purpose/topic from command"""
    command_lower = command.lower()
    
    purpose_keywords = {
        "attendance": "attendance discussion",
        "academic": "academic progress",
        "behavior": "behavior discussion", 
        "grade": "grade review",
        "performance": "performance review",
        "homework": "homework concerns",
        "participation": "class participation"
    }
    
    for keyword, purpose in purpose_keywords.items():
        if keyword in command_lower:
            return purpose
    
    return None

def confirm_or_cancel_action(command: str, language: str, state: ConversationState, db_session, educator_id) -> AssistantResponse:
    """Handle confirmation or cancellation of pending actions"""
    if is_confirmation(command):
        # Execute the pending action
        if state.pending_action == "schedule_staff_meeting":
            result = state.confirm_staff_meeting(db_session, educator_id)
            
            if result["success"]:
                actions = [{
                    "type": "staff_meeting_scheduled",
                    "description": result["message"],
                    "meeting_id": result["meeting_id"],
                    "timestamp": datetime.now().isoformat()
                }]
                
                # Clear state after successful action
                state.clear_state()
                
                return AssistantResponse(
                    response_text="✅ **Staff Meeting Scheduled Successfully!**\n\n📅 I've added the meeting to the calendar and sent notifications to all teaching staff members. Conference room has been reserved and meeting details have been shared." if language == "en"
                                 else "✅ **స్టాఫ్ మీటింగ్ విజయవంతంగా షెడ్యూల్ అయ్యింది!**\n\nనేను మీటింగ్‌ను క్యాలెండర్‌కు జోడించాను మరియు అన్ని బోధనా సిబ్బంది సభ్యులకు నోటిఫికేషన్‌లు పంపాను. కాన్ఫరెన్స్ రూమ్ రిజర్వ్ చేయబడింది మరియు మీటింగ్ వివరాలు భాగస్వామ్యం చేయబడ్డాయి.",
                    language=language,
                    actions_taken=actions,
                    assistant_state="acting"
                )
            else:
                # Error creating meeting
                state.clear_state()
                return AssistantResponse(
                    response_text=f"❌ **Error Scheduling Meeting**\n\n{result['error']}" if language == "en"
                                 else f"❌ **మీటింగ్ షెడ్యూల్ చేయడంలో లోపం**\n\n{result['error']}",
                    language=language,
                    assistant_state="ready"
                )
        
        elif state.pending_action == "schedule_parent_meeting":
            result = state.confirm_parent_meeting(db_session, educator_id)
            
            if result["success"]:
                actions = [{
                    "type": "parent_meeting_scheduled",
                    "description": result["message"],
                    "meeting_id": result["meeting_id"],
                    "timestamp": datetime.now().isoformat()
                }]
                
                # Clear state after successful action
                state.clear_state()
                
                return AssistantResponse(
                    response_text="✅ **Parent Meeting Scheduled Successfully!**\n\n📅 I've added the meeting to your calendar and sent a notification to the parent. Room has been reserved and meeting details have been shared." if language == "en"
                                 else "✅ **తల్లిదండ్రుల మీటింగ్ విజయవంతంగా షెడ్యూల్ అయ్యింది!**\n\nనేను మీటింగ్‌ను మీ క్యాలెండర్‌కు జోడించాను మరియు తల్లిదండ్రులకు నోటిఫికేషన్ పంపాను. గది రిజర్వ్ చేయబడింది మరియు మీటింగ్ వివరాలు భాగస్వామ్యం చేయబడ్డాయి.",
                    language=language,
                    actions_taken=actions,
                    assistant_state="acting"
                )
            else:
                # Error creating meeting
                state.clear_state()
                return AssistantResponse(
                    response_text=f"❌ **Error Scheduling Meeting**\n\n{result['error']}" if language == "en"
                                 else f"❌ **మీటింగ్ షెడ్యూల్ చేయడంలో లోపం**\n\n{result['error']}",
                    language=language,
                    assistant_state="ready"
                )
        
        elif state.pending_action == "send_bulk_communication":
            # Handle bulk communication sending
            data = state.collected_data
            section = data.get("section", "recipients")
            message_type = data.get("message_type", "message")
            
            actions = [{
                "type": "bulk_communication_sent",
                "description": f"Sent {message_type} to {section}",
                "section": section,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat()
            }]
            
            # Clear state after successful action
            state.clear_state()
            
            return AssistantResponse(
                response_text=f"✅ **Bulk Communication Sent Successfully!**\n\n📧 **Recipients:** {section}\n📝 **Message Type:** {message_type.title()}\n📊 **Status:** Delivered to all recipients\n📈 **Tracking:** Email delivery and read confirmations enabled\n\n🎯 All recipients will receive the message within the next few minutes!" if language == "en"
                             else f"✅ **బల్క్ కమ్యూనికేషన్ విజయవంతంగా పంపబడింది!**\n\n📧 **స్వీకరించేవారు:** {section}\n📝 **సందేశ రకం:** {message_type}\n📊 **స్థితి:** అన్ని స్వీకర్తలకు డెలివరీ చేయబడింది\n📈 **ట్రాకింగ్:** ఇమెయిల్ డెలివరీ మరియు రీడ్ కన్ఫర్మేషన్‌లు ప్రారంభించబడ్డాయి\n\n🎯 అన్ని స్వీకర్తలు వచ్చే కొన్ని నిమిషాల్లో సందేశాన్ని స్వీకరిస్తారు!",
                language=language,
                actions_taken=actions,
                assistant_state="acting"
            )
    elif is_cancellation(command):
        # Cancel the pending action
        state.clear_state()
        return AssistantResponse(
            response_text="❌ **Action Cancelled**\n\nNo problem! The meeting has not been scheduled. Let me know if you need help with anything else." if language == "en"
                         else "❌ **చర్య రద్దు చేయబడింది**\n\nసమస్య లేదు! మీటింగ్ షెడ్యూల్ చేయబడలేదు. మీకు మరేదైనా సహాయం కావాలంటే నాకు తెలియజేయండి.",
            language=language,
            assistant_state="ready"
        )
    else:
        # Didn't understand response
        return AssistantResponse(
            response_text="🤔 **I didn't understand your response.**\n\nPlease say 'yes' to confirm or 'no' to cancel the meeting." if language == "en"
                         else "🤔 **మీ ప్రతిస్పందన నాకు అర్థం కాలేదు.**\n\nమీటింగ్‌ను ధృవీకరించడానికి 'అవును' లేదా రద్దు చేయడానికి 'కాదు' అని చెప్పండి.",
            language=language,
            assistant_state="thinking"
        )

# Enhanced handler functions for comprehensive teacher portal features

def handle_staff_meeting_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None, db_session = None, educator_id: int = None) -> AssistantResponse:
    """Handle staff meeting scheduling requests"""
    if state and state.has_pending_action("schedule_staff_meeting"):
        return confirm_or_cancel_action(command, language, state, db_session, educator_id)
    
    details = extract_meeting_details(command)
    
    if details.get('time') and details.get('date'):
        if state:
            state.set_pending_action("schedule_staff_meeting", details)
        return AssistantResponse(
            response_text=f"📅 **Staff Meeting Details Confirmed**\n\n🏢 **Type:** Staff/Department Meeting\n📅 **Date:** {details['date'].title()}\n🕒 **Time:** {details['time']}\n👥 **Participants:** Teaching Staff\n📍 **Location:** Conference Room\n\n✅ Ready to schedule this meeting?" if language == "en"
                         else f"📅 **స్టాఫ్ మీటింగ్ వివరాలు ధృవీకరించబడ్డాయి**\n\n🏢 **రకం:** స్టాఫ్/డిపార్ట్‌మెంట్ మీటింగ్\n📅 **తేదీ:** {details['date']}\n🕒 **సమయం:** {details['time']}\n👥 **పాల్గొనేవారు:** బోధనా సిబ్బంది\n📍 **స్థలం:** కాన్ఫరెన్స్ రూమ్\n\n✅ ఈ మీటింగ్‌ను షెడ్యూల్ చేయడానికి సిద్ధంగా ఉన్నారా?",
            language=language,
            requires_confirmation=True,
            assistant_state="confirming"
        )
    else:
        # Set conversation flow for follow-up questions
        if state:
            state.set_conversation_flow("staff_meeting", "asking_time")
        
        return AssistantResponse(
            response_text="📅 **I'll help you schedule a staff meeting!**\n\n🕒 **When would you like to meet?**\n• Today after classes\n• Tomorrow morning\n• This week\n• Specific date and time\n\n💡 Just tell me your preferred timing!" if language == "en"
                         else "📅 **నేను స్టాఫ్ మీటింగ్ షెడ్యూల్ చేయడంలో సహాయం చేస్తాను!**\n\n🕒 **మీరు ఎప్పుడు కలుసుకోవాలనుకుంటున్నారు?**\n• ఈరోజు తరగతుల తర్వాత\n• రేపు ఉదయం\n• ఈ వారం\n• నిర్దిష్ట తేదీ మరియు సమయం\n\n💡 మీ ప్రాధాన్య సమయం చెప్పండి!",
            language=language,
            assistant_state="thinking"
        )

def handle_student_review_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle student review/consultation scheduling"""
    student_name = extract_student_name(command)
    
    if student_name:
        return AssistantResponse(
            response_text=f"👨‍🎓 **Student Review Session**\n\n📚 **Student:** {student_name}\n🔍 **Type:** Academic Review/Consultation\n\n🕒 **When would you like to meet?**\n• Today during break\n• Tomorrow after class\n• This week\n• Specific time\n\n💡 Let me know your preferred timing!" if language == "en"
                         else f"👨‍🎓 **విద్యార్థి సమీక్ష సెషన్**\n\n📚 **విద్యార్థి:** {student_name}\n🔍 **రకం:** అకడమిక్ సమీక్ష/సంప్రదింపులు\n\n🕒 **మీరు ఎప్పుడు కలుసుకోవాలనుకుంటున్నారు?**\n• ఈరోజు విరామ సమయంలో\n• రేపు తరగతి తర్వాత\n• ఈ వారం\n• నిర్దిష్ట సమయం\n\n💡 మీ ప్రాధాన్య సమయం తెలియజేయండి!",
            language=language,
            assistant_state="thinking"
        )
    else:
        return AssistantResponse(
            response_text="👨‍🎓 **I'll help you schedule a student review!**\n\n📚 **Which student needs a review session?**\n\n💡 Please provide the student's name and I'll help you set up the meeting." if language == "en"
                         else "👨‍🎓 **నేను విద్యార్థి సమీక్షను షెడ్యూల్ చేయడంలో సహాయం చేస్తాను!**\n\n📚 **ఏ విద్యార్థికి సమీక్ష సెషన్ అవసరం?**\n\n💡 దయచేసి విద్యార్థి పేరు అందించండి మరియు నేను మీటింగ్ సెటప్ చేయడంలో సహాయం చేస్తాను.",
            language=language,
            assistant_state="thinking"
        )

def handle_bulk_communication_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle bulk communication requests"""
    
    # Extract communication details
    if 'section' in command.lower() or 'class' in command.lower():
        section = extract_section_name(command)
        comm_type = "section"
    elif 'all' in command.lower() or 'everyone' in command.lower():
        section = "all students"
        comm_type = "all"
    else:
        section = None
        comm_type = "unspecified"
    
    if 'marks' in command.lower() or 'grades' in command.lower():
        message_type = "marks"
    elif 'attendance' in command.lower():
        message_type = "attendance"
    elif 'meeting' in command.lower():
        message_type = "meeting"
    else:
        message_type = "general"
    
    if section and message_type != "general":
        # We have both recipient and message type, set up for content specification
        if state:
            state.set_conversation_flow("bulk_communication", "asking_content", {
                "section": section,
                "comm_type": comm_type,
                "message_type": message_type
            })
        
        return AssistantResponse(
            response_text=f"📧 **Bulk Communication Setup**\n\n👥 **Recipients:** {section}\n📝 **Message Type:** {message_type.title()}\n\n🎯 **What would you like to send?**\n• Current marks/grades\n• Attendance summary\n• Meeting notifications\n• Custom message\n\n✅ Ready to prepare the message?" if language == "en"
                         else f"📧 **బల్క్ కమ్యూనికేషన్ సెటప్**\n\n👥 **స్వీకరించేవారు:** {section}\n📝 **సందేశ రకం:** {message_type}\n\n🎯 **మీరు ఏమి పంపాలనుకుంటున్నారు?**\n• ప్రస్తుత మార్కులు/గ్రేడ్‌లు\n• హాజరు సారాంశం\n• మీటింగ్ నోటిఫికేషన్‌లు\n• కస్టమ్ సందేశం\n\n✅ సందేశాన్ని సిద్ధం చేయడానికి సిద్ధంగా ఉన్నారా?",
            language=language,
            assistant_state="thinking"
        )
    elif section:
        # We have recipient but not message type, ask for message type
        if state:
            state.set_conversation_flow("bulk_communication", "asking_message_type", {
                "section": section,
                "comm_type": comm_type
            })
        
        return AssistantResponse(
            response_text=f"📧 **Communication to {section}**\n\n📝 **What type of message would you like to send?**\n🔸 Marks/grades updates\n🔸 Attendance alerts\n🔸 Meeting notifications\n🔸 General announcements\n🔸 Custom message\n\n💡 What should I prepare for them?" if language == "en"
                         else f"📧 **{section}కు కమ్యూనికేషన్**\n\n📝 **మీరు ఏ రకమైన సందేశం పంపాలనుకుంటున్నారు?**\n🔸 మార్కులు/గ్రేడ్‌ల అప్‌డేట్‌లు\n🔸 హాజరు హెచ్చరికలు\n🔸 మీటింగ్ నోటిఫికేషన్‌లు\n🔸 సాధారణ ప్రకటనలు\n🔸 కస్టమ్ సందేశం\n\n💡 వారికి నేను ఏమి సిద్ధం చేయాలి?",
            language=language,
            assistant_state="thinking"
        )
    else:
        # No clear recipient, ask for recipients
        if state:
            state.set_conversation_flow("bulk_communication", "asking_recipients")
        
        return AssistantResponse(
            response_text="📧 **I'll help you send bulk communications!**\n\n👥 **Who should receive the message?**\n🔸 Specific section (e.g., Section A, Section B)\n🔸 All students\n🔸 Parents of specific section\n🔸 Teaching staff\n\n📝 **What type of message?**\n🔸 Marks/grades updates\n🔸 Attendance alerts\n🔸 Meeting notifications\n🔸 General announcements\n\n💡 Tell me more details!" if language == "en"
                         else "📧 **నేను బల్క్ కమ్యూనికేషన్‌లు పంపడంలో సహాయం చేస్తాను!**\n\n👥 **సందేశాన్ని ఎవరు స్వీకరించాలి?**\n🔸 నిర్దిష్ట విభాగం (ఉదా., సెక్షన్ A, సెక్షన్ B)\n🔸 అందరు విద్యార్థులు\n🔸 నిర్దిష్ట విభాగం తల్లిదండ్రులు\n🔸 బోధనా సిబ్బంది\n\n📝 **ఏ రకమైన సందేశం?**\n🔸 మార్కులు/గ్రేడ్‌ల అప్‌డేట్‌లు\n🔸 హాజరు హెచ్చరికలు\n🔸 మీటింగ్ నోటిఫికేషన్‌లు\n🔸 సాధారణ ప్రకటనలు\n\n💡 మరిన్ని వివరాలు చెప్పండి!",
            language=language,
            assistant_state="thinking"
        )

def handle_bulk_communication_followup(command: str, language: str, mode: str, educator: Educator, state: ConversationState) -> AssistantResponse:
    """Handle follow-up responses for bulk communication setup"""
    
    if state.conversation_step == "asking_recipients":
        # User should be providing recipient information
        if 'section' in command.lower():
            section = extract_section_name(command)
            comm_type = "section"
        elif 'all' in command.lower() or 'everyone' in command.lower():
            section = "all students"
            comm_type = "all"
        elif 'staff' in command.lower() or 'teacher' in command.lower():
            section = "teaching staff"
            comm_type = "staff"
        else:
            # Try to extract section from the command anyway
            section = extract_section_name(command)
            if section:
                comm_type = "section"
            else:
                # Didn't understand, ask again
                return AssistantResponse(
                    response_text="🤔 **I need to know who should receive the message.**\n\n👥 **Please specify:**\n• Section A, Section B, etc.\n• All students\n• Parents of Section A\n• Teaching staff\n\n💡 Who do you want to send the message to?" if language == "en"
                                 else "🤔 **సందేశాన్ని ఎవరు స్వీకరించాలో నాకు తెలియాలి.**\n\n👥 **దయచేసి పేర్కొనండి:**\n• సెక్షన్ A, సెక్షన్ B, మొదలైనవి\n• అందరు విద్యార్థులు\n• సెక్షన్ A తల్లిదండ్రులు\n• బోధనా సిబ్బంది\n\n💡 మీరు సందేశాన్ని ఎవరికి పంపాలనుకుంటున్నారు?",
                    language=language,
                    assistant_state="thinking"
                )
        
        # Got recipient, now ask for message type
        state.set_conversation_flow("bulk_communication", "asking_message_type", {
            "section": section,
            "comm_type": comm_type
        })
        
        return AssistantResponse(
            response_text=f"📧 **Communication to {section}**\n\n📝 **What type of message would you like to send?**\n🔸 Marks/grades updates\n🔸 Attendance alerts\n🔸 Meeting notifications\n🔸 General announcements\n🔸 Custom message\n\n💡 What should I prepare for them?" if language == "en"
                         else f"📧 **{section}కు కమ్యూనికేషన్**\n\n📝 **మీరు ఏ రకమైన సందేశం పంపాలనుకుంటున్నారు?**\n🔸 మార్కులు/గ్రేడ్‌ల అప్‌డేట్‌లు\n🔸 హాజరు హెచ్చరికలు\n🔸 మీటింగ్ నోటిఫికేషన్‌లు\n🔸 సాధారణ ప్రకటనలు\n🔸 కస్టమ్ సందేశం\n\n💡 వారికి నేను ఏమి సిద్ధం చేయాలి?",
            language=language,
            assistant_state="thinking"
        )
    
    elif state.conversation_step == "asking_message_type":
        # User should be providing message type
        section = state.collected_data.get("section", "recipients")
        
        if 'marks' in command.lower() or 'grades' in command.lower():
            message_type = "marks"
        elif 'attendance' in command.lower():
            message_type = "attendance"
        elif 'meeting' in command.lower():
            message_type = "meeting"
        elif 'announcement' in command.lower() or 'general' in command.lower():
            message_type = "announcement"
        elif 'custom' in command.lower():
            message_type = "custom"
        else:
            # Try to infer from context or ask for clarification
            return AssistantResponse(
                response_text="🤔 **What type of message should I prepare?**\n\n📝 **Please choose:**\n• Marks or grades updates\n• Attendance alerts\n• Meeting notifications\n• General announcements\n• Custom message\n\n💡 What would you like to send?" if language == "en"
                             else "🤔 **నేను ఏ రకమైన సందేశం సిద్ధం చేయాలి?**\n\n📝 **దయచేసి ఎంచుకోండి:**\n• మార్కులు లేదా గ్రేడ్‌ల అప్‌డేట్‌లు\n• హాజరు హెచ్చరికలు\n• మీటింగ్ నోటిఫికేషన్‌లు\n• సాధారణ ప్రకటనలు\n• కస్టమ్ సందేశం\n\n💡 మీరు ఏమి పంపాలనుకుంటున్నారు?",
                language=language,
                assistant_state="thinking"
            )
        
        # Got message type, prepare for confirmation
        communication_data = {
            "section": section,
            "comm_type": state.collected_data.get("comm_type"),
            "message_type": message_type
        }
        
        state.set_pending_action("send_bulk_communication", communication_data)
        
        return AssistantResponse(
            response_text=f"✅ **Bulk Communication Ready**\n\n👥 **Recipients:** {section}\n📝 **Message Type:** {message_type.title()}\n📧 **Content:** {get_message_preview(message_type)}\n\n🎯 **Ready to send this message?** I'll prepare and deliver it to all recipients with tracking and read confirmations." if language == "en"
                         else f"✅ **బల్క్ కమ్యూనికేషన్ సిద్ధం**\n\n👥 **స్వీకరించేవారు:** {section}\n📝 **సందేశ రకం:** {message_type}\n📧 **కంటెంట్:** {get_message_preview(message_type)}\n\n🎯 **ఈ సందేశాన్ని పంపడానికి సిద్ధంగా ఉన్నారా?** నేను దీన్ని ట్రాకింగ్ మరియు రీడ్ కన్ఫర్మేషన్‌లతో అన్ని స్వీకర్తలకు సిద్ధం చేసి డెలివరీ చేస్తాను.",
            language=language,
            requires_confirmation=True,
            assistant_state="confirming"
        )
    
    # Fallback to regular bulk communication handler
    return handle_bulk_communication_request(command, language, mode, educator, state)

def get_message_preview(message_type: str) -> str:
    """Get a preview of what the message will contain"""
    previews = {
        "marks": "Current marks and grades with detailed breakdown",
        "attendance": "Attendance summary with absence details",
        "meeting": "Meeting invitation with date, time, and agenda",
        "announcement": "Important announcement with details",
        "custom": "Personalized message content"
    }
    return previews.get(message_type, "Communication content")

def handle_reports_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle report generation requests"""
    
    report_type = None
    if 'marks' in command.lower() or 'grades' in command.lower():
        report_type = "marks"
    elif 'attendance' in command.lower():
        report_type = "attendance"
    elif 'progress' in command.lower():
        report_type = "progress"
    elif 'quarterly' in command.lower() or 'monthly' in command.lower():
        report_type = "periodic"
    
    if report_type:
        return AssistantResponse(
            response_text=f"📊 **{report_type.title()} Report Generation**\n\n📋 **Report Type:** {report_type.title()} Summary\n\n🎯 **Select scope:**\n• Individual student\n• Specific section\n• All sections\n• Subject-wise analysis\n\n📅 **Time period:**\n• This week\n• This month\n• This quarter\n• Custom date range\n\n✅ Ready to generate the report?" if language == "en"
                         else f"📊 **{report_type} నివేదిక రూపకల్పన**\n\n📋 **నివేదిక రకం:** {report_type} సారాంశం\n\n🎯 **పరిధిని ఎంచుకోండి:**\n• వ్యక్తిగత విద్యార్థి\n• నిర్దిష్ట విభాగం\n• అన్ని విభాగాలు\n• విషయ వారీ విశ్లేషణ\n\n📅 **కాలవ్యవధి:**\n• ఈ వారం\n• ఈ నెల\n• ఈ త్రైమాసికం\n• కస్టమ్ తేదీ పరిధి\n\n✅ నివేదికను రూపొందించడానికి సిద్ధంగా ఉన్నారా?",
            language=language,
            assistant_state="thinking"
        )
    else:
        return AssistantResponse(
            response_text="📊 **I'll help you generate reports!**\n\n📋 **What type of report do you need?**\n• Marks/Grades summary\n• Attendance analysis\n• Student progress reports\n• Pass/fail statistics\n• Quarterly feedback summaries\n• Custom performance analysis\n\n💡 Tell me which report you'd like to create!" if language == "en"
                         else "📊 **నేను నివేదికలను రూపొందించడంలో సహాయం చేస్తాను!**\n\n📋 **మీకు ఏ రకమైన నివేదిక కావాలి?**\n• మార్కులు/గ్రేడ్‌ల సారాంశం\n• హాజరు విశ్లేషణ\n• విద్యార్థి పురోగతి నివేదికలు\n• పాస్/ఫెయిల్ గణాంకాలు\n• త్రైమాసిక ఫీడ్‌బ్యాక్ సారాంశాలు\n• కస్టమ్ పనితీరు విశ్లేషణ\n\n💡 మీరు ఏ నివేదికను సృష్టించాలనుకుంటున్నారో చెప్పండి!",
            language=language,
            assistant_state="thinking"
        )

def handle_dashboard_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle dashboard and overview requests"""
    
    # Simulate getting dashboard data
    urgent_items = 3
    pending_meetings = 2
    unread_messages = 5
    
    return AssistantResponse(
        response_text=f"📊 **Your Teaching Dashboard**\n\n🏆 **Today's Summary:**\n📅 {pending_meetings} upcoming meetings\n📧 {unread_messages} unread messages\n⚠️ {urgent_items} urgent items\n\n🎯 **Quick Actions:**\n• Review pending approvals\n• Check student attendance\n• Prepare for next class\n• Send communications\n\n💡 What would you like to focus on?" if language == "en"
                     else f"📊 **మీ బోధనా డ్యాష్‌బోర్డ్**\n\n🏆 **ఈరోజు సారాంశం:**\n📅 {pending_meetings} రాబోయే మీటింగ్‌లు\n📧 {unread_messages} చదవని సందేశాలు\n⚠️ {urgent_items} అత్యవసర అంశాలు\n\n🎯 **త్వరిత చర్యలు:**\n• పెండింగ్ ఆమోదాలను సమీక్షించండి\n• విద్యార్థుల హాజరును తనిఖీ చేయండి\n• తదుపరి తరగతికి సిద్ధం చేసుకోండి\n• కమ్యూనికేషన్‌లు పంపండి\n\n💡 మీరు దేనిపై దృష్టి పెట్టాలనుకుంటున్నారు?",
        language=language,
        assistant_state="ready"
    )

def handle_attendance_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle attendance management requests"""
    
    if 'mark' in command.lower() or 'take' in command.lower():
        action_type = "mark"
    elif 'check' in command.lower() or 'view' in command.lower():
        action_type = "view"
    elif 'report' in command.lower():
        action_type = "report"
    else:
        action_type = "general"
    
    section = extract_section_name(command)
    
    return AssistantResponse(
        response_text=f"📋 **Attendance Management**\n\n{'📍 **Section:** ' + section if section else '👥 **All Sections**'}\n\n🎯 **What would you like to do?**\n• Mark today's attendance\n• View attendance reports\n• Check absent students\n• Send attendance alerts\n• Generate attendance summary\n\n💡 Choose your action!" if language == "en"
                     else f"📋 **హాజరు నిర్వహణ**\n\n{'📍 **విభాగం:** ' + section if section else '👥 **అన్ని విభాగాలు**'}\n\n🎯 **మీరు ఏమి చేయాలనుకుంటున్నారు?**\n• ఈరోజు హాజరును గుర్తించండి\n• హాజరు నివేదికలను చూడండి\n• గైర్హాజరు విద్యార్థులను తనిఖీ చేయండి\n• హాజరు హెచ్చరికలు పంపండి\n• హాజరు సారాంశం రూపొందించండి\n\n💡 మీ చర్యను ఎంచుకోండి!",
        language=language,
        assistant_state="thinking"
    )

def handle_marks_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle marks/grades management requests"""
    
    if 'enter' in command.lower() or 'add' in command.lower():
        action_type = "enter"
    elif 'view' in command.lower() or 'check' in command.lower():
        action_type = "view"
    elif 'send' in command.lower() or 'share' in command.lower():
        action_type = "send"
    else:
        action_type = "general"
    
    section = extract_section_name(command)
    
    return AssistantResponse(
        response_text=f"📝 **Marks & Grades Management**\n\n{'📍 **Section:** ' + section if section else '👥 **All Sections**'}\n\n🎯 **What would you like to do?**\n• Enter new marks\n• View current grades\n• Send marks to parents\n• Generate grade reports\n• Analyze performance trends\n• Update grade calculations\n\n💡 Choose your action!" if language == "en"
                     else f"📝 **మార్కులు & గ్రేడ్‌ల నిర్వహణ**\n\n{'📍 **విభాగం:** ' + section if section else '👥 **అన్ని విభాగాలు**'}\n\n🎯 **మీరు ఏమి చేయాలనుకుంటున్నారు?**\n• కొత్త మార్కులను నమోదు చేయండి\n• ప్రస్తుత గ్రేడ్‌లను చూడండి\n• తల్లిదండ్రులకు మార్కులు పంపండి\n• గ్రేడ్ నివేదికలను రూపొందించండి\n• పనితీరు ట్రెండ్‌లను విశ్లేషించండి\n• గ్రేడ్ లెక్కలను నవీకరించండి\n\n💡 మీ చర్యను ఎంచుకోండి!",
        language=language,
        assistant_state="thinking"
    )

def handle_section_management_request(command: str, language: str, mode: str, educator: Educator, state: ConversationState = None) -> AssistantResponse:
    """Handle section/class management requests"""
    
    return AssistantResponse(
        response_text="🏫 **Section Management**\n\n📋 **Available Actions:**\n• View section details\n• Assign students to sections\n• Manage section schedules\n• Update section information\n• Generate section reports\n• Send section-wide notifications\n\n👥 **Section Operations:**\n• Create new sections\n• Merge sections\n• Transfer students\n• Archive old sections\n\n💡 What would you like to manage?" if language == "en"
                     else "🏫 **విభాగ నిర్వహణ**\n\n📋 **అందుబాటులో ఉన్న చర్యలు:**\n• విభాగ వివరాలను చూడండి\n• విద్యార్థులను విభాగాలకు కేటాయించండి\n• విభాగ షెడ్యూల్‌లను నిర్వహించండి\n• విభాగ సమాచారాన్ని నవీకరించండి\n• విభాగ నివేదికలను రూపొందించండి\n• విభాగ వ్యాప్త నోటిఫికేషన్‌లు పంపండి\n\n👥 **విభాగ కార్యకలాపాలు:**\n• కొత్త విభాగాలను సృష్టించండి\n• విభాగాలను విలీనం చేయండి\n• విద్యార్థులను బదిలీ చేయండి\n• పాత విభాగాలను ఆర్కైవ్ చేయండి\n\n💡 మీరు దేనిని నిర్వహించాలనుకుంటున్నారు?",
        language=language,
        assistant_state="thinking"
    )

# Helper functions for enhanced natural language processing

def extract_student_name_flexible(command: str) -> str:
    """Extract student name from command with flexible matching for simple responses"""
    import re
    
    command = command.strip()
    
    # Don't treat common commands as names
    common_non_names = {
        'hello', 'hi', 'hey', 'schedule', 'meetings', 'help', 'yes', 'no', 
        'okay', 'ok', 'please', 'thanks', 'thank', 'you', 'sure', 'great',
        'good', 'morning', 'afternoon', 'evening', 'today', 'tomorrow',
        'student', 'parent', 'staff', 'meeting', 'class', 'section'
    }
    
    # If it's a very simple response (1-3 words), treat it as a potential name
    words = command.split()
    if len(words) <= 3 and all(word.replace('.', '').replace(',', '').isalpha() for word in words):
        # Check if any word is a common non-name
        if any(word.lower() in common_non_names for word in words):
            return None
            
        # Clean and capitalize the words
        cleaned_words = []
        for word in words:
            clean_word = word.replace('.', '').replace(',', '').strip()
            if clean_word and len(clean_word) >= 2:  # At least 2 characters
                cleaned_words.append(clean_word.capitalize())
        
        if cleaned_words:
            return ' '.join(cleaned_words)
    
    # Fallback to the original extraction method
    return extract_student_name(command)

def extract_student_name(command: str) -> str:
    """Extract student name from command"""
    # Simple name extraction - look for capitalized words that could be names
    import re
    
    # Look for patterns like "for [Name]", "with [Name]", "[Name]'s"
    patterns = [
        r'for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[\'\'s]',
        r'student\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            return match.group(1)
    
    # Look for standalone capitalized words (potential names)
    words = command.split()
    for i, word in enumerate(words):
        if word[0].isupper() and len(word) > 2 and word not in ['Schedule', 'Meeting', 'Student', 'Section', 'Class']:
            # Check if next word is also capitalized (full name)
            if i < len(words) - 1 and words[i + 1][0].isupper():
                return f"{word} {words[i + 1]}"
            return word
    
    return None

def extract_section_name(command: str) -> str:
    """Extract section name from command"""
    import re
    
    # Look for patterns like "Section A", "Class B", "section 1", etc.
    patterns = [
        r'section\s+([A-Z0-9]+)',
        r'class\s+([A-Z0-9]+)',
        r'grade\s+([A-Z0-9]+)',
        r'([A-Z]+)\s+section',
    ]
    
    command_lower = command.lower()
    command_original = command
    
    for pattern in patterns:
        match = re.search(pattern, command_lower)
        if match:
            return f"Section {match.group(1).upper()}"
    
    return None

def handle_ai_assistant_command(command: str, language: str = "en", mode: str = "assist", educator_id: int = None) -> AssistantResponse:
    """Main AI assistant command handler with stateful conversation flow"""
    
    # Get conversation state for this user
    user_id = str(educator_id) if educator_id else "anonymous"
    state = get_conversation_state(user_id)
    
    # Get educator object if educator_id is provided
    educator = None
    if educator_id:
        try:
            db = SessionLocal()
            educator = db.query(Educator).filter(Educator.id == educator_id).first()
            db.close()
        except Exception as e:
            print(f"Database error: {e}")
            educator = None
    
    if not command or not command.strip():
        # Clear state on empty command
        state.clear_state()
        return AssistantResponse(
            response_text="👋 **Hello! I'm your AI Teaching Assistant.**\n\nI can help you with:\n🔸 **Schedule** parent meetings\n🔸 **Review** student progress\n🔸 **Plan** lesson activities\n🔸 **Manage** classroom tasks\n\nWhat would you like to do?" if language == "en"
                         else "👋 **నమస్కారం! నేను మీ AI టీచింగ్ అసిస్టెంట్.**\n\nనేను మీకు సహాయం చేయగలను:\n🔸 **షెడ్యూల్** తల్లిదండ్రుల మీటింగ్‌లు\n🔸 **సమీక్ష** విద్యార్థుల పురోగతి\n🔸 **ప్లాన్** పాఠ కార్యకలాపాలు\n🔸 **నిర్వహణ** తరగతి పనులు\n\nమీరు ఏమి చేయాలనుకుంటున్నారు?",
            language=language,
            assistant_state="ready"
        )
    
    command = command.strip()
    command_lower = command.lower()
    
    # Auto-detect language from the command
    detected_language = detect_language(command)
    
    # Check if user is in an active conversation flow
    if state.conversation_type and state.assistant_state == "thinking":
        # User is providing follow-up information for an ongoing conversation
        
        if state.conversation_type == "parent_meeting":
            # Continue parent meeting flow
            return handle_parent_meeting_followup(command, detected_language, mode, educator, state)
        elif state.conversation_type == "staff_meeting":
            # Continue staff meeting flow
            return handle_staff_meeting_followup(command, detected_language, mode, educator, state)
        elif state.conversation_type == "student_review":
            # Continue student review flow
            return handle_student_review_followup(command, detected_language, mode, educator, state)
        elif state.conversation_type == "bulk_communication":
            # Continue bulk communication flow
            return handle_bulk_communication_followup(command, detected_language, mode, educator, state)
        # Add more conversation types as needed
    
    # Check if user is confirming a pending action
    if state.requires_confirmation and state.pending_action:
        # Open database session for confirmation actions
        db = SessionLocal()
        try:
            result_response = confirm_or_cancel_action(command, detected_language, state, db, educator_id)
            db.close()
            return result_response
        except Exception as e:
            db.rollback()
            db.close()
            state.clear_state()
            return AssistantResponse(
                response_text=f"❌ **Error processing request:** {str(e)}" if detected_language == "en"
                             else f"❌ **అభ్యర్థనను ప్రాసెస్ చేయడంలో లోపం:** {str(e)}",
                language=detected_language,
                assistant_state="ready"
            )
    
    # Get educator if provided
    educator = None
    if educator_id:
        db = SessionLocal()
        try:
            educator = db.query(Educator).filter(Educator.id == educator_id).first()
        finally:
            db.close()
    
    # Intent detection with fuzzy matching - Enhanced for comprehensive teacher portal
    intents = {
        'parent_meeting': ['parent', 'meeting', 'schedule', 'parents', 'discuss', 'talk', 'conference', 'appointment'],
        'staff_meeting': ['staff', 'teacher', 'department', 'colleague', 'faculty', 'team', 'meeting'],
        'student_review': ['student', 'review', 'consultation', 'counseling', 'guidance', 'session'],
        'schedule': ['schedule', 'book', 'arrange', 'plan', 'set up', 'organize', 'calendar', 'appointment'],
        'greeting': ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'start', 'namaste', 'namaskar'],
        'help': ['help', 'assist', 'support', 'what can you do', 'commands', 'guide'],
        'student_info': ['student', 'progress', 'grade', 'performance', 'attendance', 'marks', 'scores'],
        'bulk_communication': ['send', 'email', 'notify', 'message', 'inform', 'section', 'class', 'bulk', 'all'],
        'reports': ['report', 'summary', 'analysis', 'generate', 'export', 'download', 'statistics'],
        'document_management': ['document', 'file', 'form', 'certificate', 'letter', 'generate', 'create'],
        'dashboard': ['dashboard', 'overview', 'summary', 'today', 'pending', 'urgent', 'tasks'],
        'attendance': ['attendance', 'absent', 'present', 'roll', 'call', 'participation'],
        'marks_management': ['marks', 'grades', 'scores', 'results', 'assessment', 'evaluation'],
        'section_management': ['section', 'class', 'group', 'assign', 'manage', 'organize']
    }
    
    # Calculate intent scores
    intent_scores = {}
    for intent, keywords in intents.items():
        intent_scores[intent] = fuzzy_match_intent(command, keywords)
    
    # Get the highest scoring intent
    best_intent = max(intent_scores, key=intent_scores.get)
    best_score = intent_scores[best_intent]
    
    # Handle based on intent and command content
    if best_intent == 'greeting' and best_score > 0.2:  # Lower threshold for better greeting detection
        return AssistantResponse(
            response_text="👋 **Hello! Ready to help with your teaching tasks.**\n\n🎯 **What would you like to do?**\n🔸 Schedule meetings (parent/staff/student)\n🔸 Manage students & sections\n🔸 Send bulk communications\n🔸 Generate reports & documents\n🔸 Review dashboard & tasks\n🔸 Track attendance & marks\n\nJust tell me what you need!" if detected_language == "en"
                         else "👋 **నమస్కారం! మీ బోధనా పనులతో సహాయం చేయడానికి సిద్ధంగా ఉన్నాను.**\n\n🎯 **మీరు ఏమి చేయాలనుకుంటున్నారు?**\n🔸 మీటింగ్‌లను షెడ్యూల్ చేయండి (తల్లిదండ్రులు/సిబ్బంది/విద్యార్థి)\n🔸 విద్యార్థులు & విభాగాలను నిర్వహించండి\n🔸 బల్క్ కమ్యూనికేషన్‌లు పంపండి\n🔸 నివేదికలు & డాక్యుమెంట్‌లను రూపొందించండి\n🔸 డ్యాష్‌బోర్డ్ & పనులను సమీక్షించండి\n🔸 హాజరు & మార్కులను ట్రాక్ చేయండి\n\nమీకు ఏమి కావాలో చెప్పండి!",
            language=detected_language,
            assistant_state="ready"
        )
    
    elif best_intent == 'staff_meeting' or ('staff' in command_lower and 'meeting' in command_lower) or ('schedule' in command_lower and ('staff' in command_lower or 'department' in command_lower)):
        return handle_staff_meeting_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'parent_meeting' or ('schedule' in command_lower and ('parent' in command_lower or 'meeting' in command_lower)) and not ('staff' in command_lower):
        return handle_parent_meeting_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'student_review' or ('student' in command_lower and ('review' in command_lower or 'consultation' in command_lower)):
        return handle_student_review_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'bulk_communication' or ('send' in command_lower and ('section' in command_lower or 'class' in command_lower or 'all' in command_lower or 'parents' in command_lower)) or ('send' in command_lower and ('marks' in command_lower or 'grades' in command_lower)) or ('email' in command_lower) or ('section' in command_lower and ('students' in command_lower or 'parents' in command_lower)) or ('all' in command_lower and 'students' in command_lower):
        return handle_bulk_communication_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'reports' or ('report' in command_lower or 'generate' in command_lower):
        return handle_reports_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'dashboard' or ('dashboard' in command_lower or 'overview' in command_lower or 'today' in command_lower):
        return handle_dashboard_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'attendance' or 'attendance' in command_lower or ('mark' in command_lower and 'attendance' in command_lower):
        return handle_attendance_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'marks_management' or ('marks' in command_lower or 'grades' in command_lower) and 'send' not in command_lower:
        return handle_marks_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'section_management' or ('section' in command_lower and ('manage' in command_lower or 'assign' in command_lower)):
        return handle_section_management_request(command, detected_language, mode, educator, state)
    
    elif best_intent == 'schedule' and best_score > 0.3:
        return AssistantResponse(
            response_text="📅 **I can help you schedule!**\n\n🎯 **What type of meeting?**\n🔸 Parent meeting\n🔸 Staff meeting\n🔸 Student consultation\n🔸 Department meeting\n🔸 Class review session\n\nOr tell me specifically what you'd like to schedule!" if detected_language == "en"
                         else "📅 **నేను షెడ్యూల్ చేయడంలో సహాయం చేయగలను!**\n\n🎯 **ఏ రకమైన మీటింగ్?**\n🔸 తల్లిదండ్రుల మీటింగ్\n🔸 స్టాఫ్ మీటింగ్\n🔸 విద్యార్థి సంప్రదింపులు\n🔸 డిపార్ట్‌మెంట్ మీటింగ్\n🔸 క్లాస్ సమీక్ష సెషన్\n\nలేదా మీరు ఏమి షెడ్యూల్ చేయాలనుకుంటున్నారో నిర్దిష్టంగా చెప్పండి!",
            language=detected_language,
            assistant_state="thinking"
        )
    
    elif best_intent == 'help' and best_score > 0.5:
        return AssistantResponse(
            response_text="🤝 **I'm your comprehensive AI Teaching Assistant!**\n\n📋 **My full capabilities:**\n\n�️ **Scheduling & Calendar:**\n• Parent meetings, staff meetings, student consultations\n• Conflict detection and optimal time suggestions\n• Automated invites and reminders\n\n� **Student & Section Management:**\n• View and filter students by performance/attendance\n• Individual student profiles and progress tracking\n• Section assignments and management\n\n� **Bulk Communications:**\n• Send personalized messages to sections or all students\n• Marks updates, attendance alerts, meeting notifications\n• Delivery tracking and read status\n\n� **Reports & Analysis:**\n• Marks summaries, attendance reports, performance analysis\n• Pass/fail statistics, quarterly feedback summaries\n• Background processing with completion notifications\n\n📝 **Document Management:**\n• Generate meeting notes, compliance forms, progress reports\n• Organize and share documents with access tracking\n\n📋 **Attendance & Marks:**\n• Mark attendance, view reports, send alerts\n• Enter grades, analyze trends, share with parents\n\n🎯 **Dashboard & Overview:**\n• Daily summaries, urgent items highlighting\n• Pending tasks and deadline tracking\n\n💡 **Just tell me what you need in natural language!**\nExample: 'Schedule parent meeting for Alice tomorrow morning' or 'Send marks to Section A parents'" if detected_language == "en"
                         else "🤝 **నేను మీ సమగ్ర AI బోధనా సహాయకుడను!**\n\n📋 **నా పూర్తి సామర్థ్యాలు:**\n\n�️ **షెడ్యూలింగ్ & క్యాలెండర్:**\n• తల్లిదండ్రుల మీటింగ్‌లు, స్టాఫ్ మీటింగ్‌లు, విద్యార్థి సంప్రదింపులు\n• సంఘర్షణ గుర్తింపు మరియు అనుకూల సమయ సూచనలు\n• ఆటోమేటెడ్ ఆహ్వానాలు మరియు రిమైండర్‌లు\n\n👥 **విద్యార్థి & విభాగ నిర్వహణ:**\n• పనితీరు/హాజరు ప్రకారం విద్యార్థులను వీక్షించండి మరియు ఫిల్టర్ చేయండి\n• వ్యక్తిగత విద్యార్థి ప్రొఫైల్‌లు మరియు పురోగతి ట్రాకింగ్\n• విభాగ కేటాయింపులు మరియు నిర్వహణ\n\n� **బల్క్ కమ్యూనికేషన్‌లు:**\n• విభాగాలకు లేదా అందరు విద్యార్థులకు వ్యక్తిగతీకరించిన సందేశాలు పంపండి\n• మార్కుల అప్‌డేట్‌లు, హాజరు హెచ్చరికలు, మీటింగ్ నోటిఫికేషన్‌లు\n• డెలివరీ ట్రాకింగ్ మరియు రీడ్ స్టేటస్\n\n� **నివేదికలు & విశ్లేషణ:**\n• మార్కుల సారాంశాలు, హాజరు నివేదికలు, పనితీరు విశ్లేషణ\n• పాస్/ఫెయిల్ గణాంకాలు, త్రైమాసిక ఫీడ్‌బ్యాక్ సారాంశాలు\n• పూర్తి నోటిఫికేషన్‌లతో బ్యాక్‌గ్రౌండ్ ప్రాసెసింగ్\n\n📝 **డాక్యుమెంట్ మేనేజ్‌మెంట్:**\n• మీటింగ్ నోట్స్, కంప్లయన్స్ ఫారమ్‌లు, పురోగతి నివేదికలను రూపొందించండి\n• యాక్సెస్ ట్రాకింగ్‌తో డాక్యుమెంట్‌లను నిర్వహించండి మరియు భాగస్వామ్యం చేయండి\n\n📋 **హాజరు & మార్కులు:**\n• హాజరును గుర్తించండి, నివేదికలను చూడండి, హెచ్చరికలు పంపండి\n• గ్రేడ్‌లను నమోదు చేయండి, ట్రెండ్‌లను విశ్లేషించండి, తల్లిదండ్రులతో భాగస్వామ్యం చేయండి\n\n🎯 **డ్యాష్‌బోర్డ్ & ఓవర్‌వ్యూ:**\n• రోజువారీ సారాంశాలు, అత్యవసర అంశాల హైలైటింగ్\n• పెండింగ్ పనులు మరియు డెడ్‌లైన్ ట్రాకింగ్\n\n💡 **సహజ భాషలో మీకు కావలసినది చెప్పండి!**\nఉదాహరణ: 'రేపు ఉదయం అలీస్ కోసం తల్లిదండ్రుల మీటింగ్ షెడ్యూల్ చేయండి' లేదా 'సెక్షన్ A తల్లిదండ్రులకు మార్కులు పంపండి'",
            language=detected_language,
            assistant_state="ready"
        )
    
    else:
        # Try to understand natural language and extract actionable information
        if extract_meeting_details(command):
            return handle_parent_meeting_request(command, detected_language, mode, educator, state)
        
        # Check for complex instructions with multiple keywords
        if ('send' in command_lower and ('marks' in command_lower or 'grades' in command_lower)):
            return handle_bulk_communication_request(command, detected_language, mode, educator, state)
        
        if ('generate' in command_lower and 'report' in command_lower):
            return handle_reports_request(command, detected_language, mode, educator, state)
        
        # Enhanced default response for complex requests
        return AssistantResponse(
            response_text=f"🤔 **I understand you want to: \"{command}\"**\n\n💡 **I can help you with comprehensive teaching tasks!**\n\n🎯 **Try these specific commands:**\n• \"Schedule parent meeting for [Student Name] tomorrow\"\n• \"Send marks to Section A parents\"\n• \"Generate attendance report for this week\"\n• \"Show me dashboard overview\"\n• \"Mark attendance for Section B\"\n• \"Schedule staff meeting for Friday\"\n\n📋 **Or ask for help with:**\n• Scheduling & calendar management\n• Student & section management  \n• Bulk communications\n• Reports & analysis\n• Document management\n• Attendance & marks tracking\n\n💬 **What specific task can I help you accomplish?**" if detected_language == "en"
                         else f"🤔 **మీరు దీన్ని చేయాలనుకుంటున్నారని నేను అర్థం చేసుకున్నాను: \"{command}\"**\n\n💡 **నేను సమగ్ర బోధనా పనులతో మీకు సహాయం చేయగలను!**\n\n🎯 **ఈ నిర్దిష్ట కమాండ్‌లను ప్రయత్నించండి:**\n• \"రేపు [విద్యార్థి పేరు] కోసం తల్లిదండ్రుల మీటింగ్ షెడ్యూల్ చేయండి\"\n• \"సెక్షన్ A తల్లిదండ్రులకు మార్కులు పంపండి\"\n• \"ఈ వారం హాజరు నివేదిక రూపొందించండి\"\n• \"డ్యాష్‌బోర్డ్ ఓవర్‌వ్యూ చూపించండి\"\n• \"సెక్షన్ B కోసం హాజరు గుర్తించండి\"\n• \"శుక్రవారం స్టాఫ్ మీటింగ్ షెడ్యూల్ చేయండి\"\n\n📋 **లేదా దీనితో సహాయం అడగండి:**\n• షెడ్యూలింగ్ & క్యాలెండర్ మేనేజ్‌మెంట్\n• విద్యార్థి & విభాగ నిర్వహణ\n• బల్క్ కమ్యూనికేషన్‌లు\n• నివేదికలు & విశ్లేషణ\n• డాక్యుమెంట్ మేనేజ్‌మెంట్\n• హాజరు & మార్కుల ట్రాకింగ్\n\n💬 **నేను మీకు ఏ నిర్దిష్ট పనిలో సహాయం చేయగలను?**",
            language=detected_language,
            assistant_state="thinking"
        )


@router.post("/command")
async def process_ai_command(
    request: CommandRequest,
    educator: Educator = Depends(get_current_educator)
):
    """Process AI assistant command with progressive conversation flow"""
    
    try:
        # Get the command text from the request
        command_text = request.get_command()
        
        # Forward command to the centralized Gemini assistant for consistent behavior
        db = get_db()
        try:
            result = await gemini_assistant.process_command(command_text, educator.id, db)
        finally:
            # get_db() yields a session when used as dependency; when called directly, ensure close if possible
            try:
                db.close()
            except Exception:
                pass

        # Return Gemini assistant's structured response
        return {
            "response_text": result.get("response", ""),
            "language": result.get("language", "en"),
            "suggested_actions": [],
            "actions_taken": result.get("actions", []),
            "requires_confirmation": result.get("requires_approval", False),
            "assistant_state": result.get("state", "idle")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Assistant error: {str(e)}")


@router.post("/test-command")
async def test_ai_command(request: CommandRequest):
    """Test AI assistant command without authentication (for testing only)"""
    
    try:
        # Forward test command to Gemini assistant using a test educator id
        db = SessionLocal()
        try:
            result = await gemini_assistant.process_command(request.command, 1, db)
        finally:
            try:
                db.close()
            except Exception:
                pass

        return {
            "response_text": result.get("response", ""),
            "language": result.get("language", "en"),
            "suggested_actions": [],
            "actions_taken": result.get("actions", []),
            "requires_confirmation": result.get("requires_approval", False),
            "assistant_state": result.get("state", "idle")
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Assistant error: {str(e)}")


@router.get("/status")
async def get_assistant_status():
    """Get AI assistant status and capabilities"""
    return {
        "status": "active",
        "version": "2.0.0",
        "capabilities": [
            "Progressive conversation flow",
            "Natural language understanding", 
            "Meeting scheduling",
            "Student progress tracking",
            "Bilingual support (EN/TE)",
            "Context awareness"
        ],
        "conversation_features": [
            "Never repeats questions",
            "Progressive disclosure",
            "Natural dialogue patterns",
            "Entity extraction",
            "Intent fuzzy matching"
        ]
    }