"""
Advanced AI Assistant with Google Gemini integration
Supports three autonomy modes: Manual, Assist, Autonomous
Multilingual support (English/Telugu)
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import google.generativeai as genai
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.educator import Educator
from app.models.student import Student, Section, Grade

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class AutonomyMode(str, Enum):
    MANUAL = "manual"
    ASSIST = "assist"
    AUTONOMOUS = "autonomous"

class AssistantState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING_APPROVAL = "waiting_approval"

class Language(str, Enum):
    ENGLISH = "en"
    TELUGU = "te"

class ActionType(str, Enum):
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"

class GeminiEducatorAssistant:
    """Advanced AI Assistant powered by Google Gemini"""
    
    def __init__(self):
        # Use model from settings if provided
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-pro')
        try:
            self.model = genai.GenerativeModel(model_name)
        except Exception:
            # Fallback to a known stable model
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.state = AssistantState.IDLE
        # Default to AUTONOMOUS so the assistant performs requested actions without asking
        # (low/medium risk actions are executed automatically in AUTONOMOUS mode)
        self.autonomy_mode = AutonomyMode.AUTONOMOUS
        self.language = Language.ENGLISH
        self.action_log = []
        
        # System prompts for different contexts
        self.system_prompts = {
            "base": """You are EduAssist AI, an intelligent administrative assistant for educators. 
            You help teachers manage their administrative tasks efficiently. 
            Always be helpful, professional, and focused on educational administration.
            
            Current autonomy mode: {autonomy_mode}
            Language preference: {language}
            
            You can perform these actions:
            - Calendar management (schedule meetings, check conflicts)
            - Email composition and sending
            - Student performance analysis
            - Report generation
            - Compliance documentation
            - Administrative task automation
            
            Based on autonomy mode:
            - Manual: Always ask for confirmation before any action
            - Assist: Perform low-risk tasks automatically, ask for medium/high-risk
            - Autonomous: Perform all allowed actions automatically
            """,
            
            "intent_analysis": """Analyze the user's intent and classify it. 
            Return a JSON with:
            {
                "intent": "string",
                "action_type": "low_risk|medium_risk|high_risk",
                "entities": {},
                "confidence": 0.8,
                "requires_data": ["calendar", "students", "grades"],
                "suggested_actions": []
            }""",
            
            "telugu_support": """You can understand and respond in both English and Telugu.
            Telugu phrases you should recognize:
            - "నా షెడ్యూల్ చూపించు" (show my schedule)
            - "విద్యార్థుల గ్రేడ్స్ చూపించు" (show student grades)
            - "ఇమెయిల్ పంపించు" (send email)
            - "రిపోర్ట్ తయారు చేయి" (generate report)
            """
        }
    
    def set_autonomy_mode(self, mode: AutonomyMode):
        """Set the assistant's autonomy mode"""
        self.autonomy_mode = mode
        self.log_action("system", f"Autonomy mode changed to {mode}")
    
    def set_language(self, language: Language):
        """Set the language preference"""
        self.language = language
        self.log_action("system", f"Language changed to {language}")
    
    def log_action(self, action_type: str, description: str, metadata: Dict = None):
        """Log assistant actions for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "description": description,
            "metadata": metadata or {},
            "autonomy_mode": self.autonomy_mode,
            "language": self.language
        }
        self.action_log.append(log_entry)
    
    async def analyze_intent(self, user_input: str, educator_id: int) -> Dict[str, Any]:
        """Enhanced intelligent intent analysis using Gemini"""
        self.state = AssistantState.THINKING
        
        # Enhanced prompt for better intent recognition
        prompt = f"""
        You are EduAssist AI, analyzing a teacher's natural language command. 
        
        IMPORTANT: Understand the teacher's intent even from casual, conversational input.
        
        Teacher said: "{user_input}"
        
        Analyze this and return ONLY a JSON object with this exact structure:
        {{
            "intent": "specific_action_name",
            "action_type": "low_risk|medium_risk|high_risk",
            "entities": {{
                "section": "extracted_section_if_any",
                "subject": "extracted_subject_if_any", 
                "student": "extracted_student_if_any",
                "time_frame": "extracted_time_period",
                "report_type": "extracted_report_type",
                "number": "extracted_number_if_any"
            }},
            "confidence": 0.9,
            "requires_data": ["students", "grades", "attendance"],
            "suggested_actions": ["show_student_list", "generate_report"],
            "natural_response": "I'll show you the top 5 students from Section A right away!"
        }}
        
        INTENT CATEGORIES TO RECOGNIZE:
        
        🎯 STUDENT QUERIES:
        - "show me students", "get student list", "who are my students" → "list_students"
        - "top students", "best performers", "highest marks" → "show_top_performers"  
        - "failing students", "low performers", "students below 50" → "show_struggling_students"
        - "students who missed classes", "absent students" → "show_attendance_issues"
        
        📊 PERFORMANCE ANALYSIS:
        - "analyze performance", "how is Section A doing" → "analyze_section_performance"
        - "grade summary", "marks overview" → "show_grade_summary"
        - "compare sections", "which section is better" → "compare_section_performance"
        - "subject performance", "how is math going" → "analyze_subject_performance"
        
        📧 COMMUNICATION:
        - "send email", "notify parents", "send message" → "send_communication"
        - "remind about", "send reminder" → "send_reminder"
        - "appreciation mail", "congratulate students" → "send_appreciation"
        
        📅 SCHEDULING:
        - "schedule meeting", "book appointment", "meet parent" → "schedule_meeting"
        - "my schedule", "show calendar", "what's next" → "show_schedule"
        - "free time", "when am I available" → "check_availability"
        
        📋 REPORTS:
        - "generate report", "create summary", "make report" → "generate_report"
        - "attendance report", "attendance summary" → "attendance_report"
        - "performance report", "grade report" → "performance_report"
        
        EXTRACT ENTITIES:
        - Sections: "Section A", "Section B", "Class C", "my sections"
        - Subjects: "Math", "Science", "English", "Physics", "Chemistry" 
        - Numbers: "top 5", "below 50%", "more than 3 days"
        - Time: "this week", "last month", "October", "today"
        
        RISK LEVELS:
        - low_risk: Viewing data, showing reports, analyzing performance
        - medium_risk: Sending emails, scheduling meetings
        - high_risk: Changing grades, deleting data, bulk operations
        
        MULTILINGUAL SUPPORT:
        Also recognize Telugu commands:
        - "విద్యార్థుల జాబితా చూపించు" → "list_students"
        - "గ్రేడ్స్ చూపించు" → "show_grades"
        - "రిపోర్ట్ తయారు చేయి" → "generate_report"
        - "ఇమెయిల్ పంపించు" → "send_communication"
        
        Return only the JSON, no other text.
        """
        
        try:
            response = await self._call_gemini(prompt)
            intent_data = self._parse_json_response(response)
            
            # Validate and enhance the response
            intent_data = self._enhance_intent_data(intent_data, user_input)
            
            self.log_action("intent_analysis", f"Analyzed: {user_input}", intent_data)
            return intent_data
            
        except Exception as e:
            self.log_action("error", f"Intent analysis failed: {str(e)}")
            return self._fallback_intent_analysis(user_input)
    
    async def process_command(self, user_input: str, educator_id: int, db: Session, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Main command processing pipeline"""
        try:
            # Step 1: Analyze intent
            intent = await self.analyze_intent(user_input, educator_id)
            
            # Step 2: Gather required data
            context_data = await self._gather_context_data(intent["requires_data"], educator_id, db)
            
            # Step 3: Generate response and actions (include conversation history)
            response = await self._generate_response(user_input, intent, context_data, educator_id, conversation_history)
            
            # Step 4: Execute actions based on autonomy mode (pass DB and educator id)
            executed_actions = await self._execute_actions(response["actions"], intent["action_type"], db, educator_id)
            
            self.state = AssistantState.IDLE
            
            return {
                "response": response["message"],
                "actions": executed_actions,
                "state": self.state,
                "requires_approval": response.get("requires_approval", False),
                "audit_log": self.action_log[-5:],  # Last 5 actions
                "language": self.language
            }
            
        except Exception as e:
            self.state = AssistantState.IDLE
            self.log_action("error", f"Command processing failed: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "actions": [],
                "state": self.state,
                "requires_approval": False,
                "audit_log": self.action_log[-5:],
                "language": self.language
            }
    
    async def _gather_context_data(self, required_data: List[str], educator_id: int, db: Session) -> Dict[str, Any]:
        """Gather relevant context data for processing"""
        context = {}
        
        try:
            if "calendar" in required_data:
                # Mock calendar data - in real implementation, integrate with Google Calendar
                context["calendar"] = {
                    "today_events": [],
                    "upcoming_events": [],
                    "conflicts": []
                }
            
            if "students" in required_data or "sections" in required_data:
                # Get educator's sections and students
                from app.models.student import Section, Student
                sections = db.query(Section).filter(Section.educator_id == educator_id).all()
                students_data = []
                sections_data = []
                
                for section in sections:
                    sections_data.append({
                        "id": section.id,
                        "name": section.name,
                        "student_count": len(section.students)
                    })
                    
                    students = db.query(Student).filter(Student.section_id == section.id).all()
                    for student in students:
                        students_data.append({
                            "id": student.id,
                            "name": student.full_name,
                            "email": student.email,
                            "section": section.name,
                            "section_id": section.id,
                            "roll_number": student.roll_number
                        })
                
                context["students"] = students_data
                context["sections"] = sections_data
            
            if "grades" in required_data:
                # Get recent grade data for educator's students
                from app.models.student import Grade, Subject
                grades_query = db.query(Grade).join(Student).join(Section).filter(
                    Section.educator_id == educator_id
                ).order_by(Grade.created_at.desc()).limit(200).all()
                
                grades_data = []
                for grade in grades_query:
                    grades_data.append({
                        "student_id": grade.student_id,
                        "student_name": grade.student.full_name,
                        "subject_id": grade.subject_id,
                        "subject_name": grade.subject.name if grade.subject else "Unknown",
                        "marks_obtained": grade.marks_obtained,
                        "total_marks": grade.total_marks,
                        "percentage": grade.percentage,
                        "grade_letter": grade.grade_letter,
                        "assessment_type": grade.assessment_type,
                        "is_passed": grade.is_passed
                    })
                
                context["grades"] = grades_data
            
            if "subjects" in required_data:
                # Get subjects for educator's sections
                from app.models.student import Subject
                subjects_query = db.query(Subject).join(Section).filter(
                    Section.educator_id == educator_id
                ).all()
                
                subjects_data = []
                for subject in subjects_query:
                    subjects_data.append({
                        "id": subject.id,
                        "name": subject.name,
                        "code": subject.code,
                        "section": subject.section.name,
                        "credits": subject.credits,
                        "passing_grade": subject.passing_grade
                    })
                
                context["subjects"] = subjects_data
            
            if "attendance" in required_data:
                # Get attendance data
                from app.models.performance import Attendance
                attendance_query = db.query(Attendance).join(Student).join(Section).filter(
                    Section.educator_id == educator_id
                ).order_by(Attendance.date.desc()).limit(500).all()
                
                attendance_data = []
                for record in attendance_query:
                    attendance_data.append({
                        "student_id": record.student_id,
                        "student_name": record.student.full_name,
                        "date": record.date.isoformat(),
                        "present": record.present,
                        "subject": record.subject.name if record.subject else None,
                        "remarks": record.remarks
                    })
                
                context["attendance"] = attendance_data
            
            if "communications" in required_data:
                # Get recent communications
                from app.models.communication import Communication
                communications = db.query(Communication).filter(
                    Communication.sender_email.like(f"%{educator_id}%")
                ).order_by(Communication.sent_at.desc()).limit(50).all()
                
                context["communications"] = [
                    {
                        "recipient": comm.recipient_email,
                        "subject": comm.subject,
                        "content": comm.content[:100] + "..." if len(comm.content) > 100 else comm.content,
                        "sent_at": comm.sent_at.isoformat(),
                        "status": comm.status
                    } for comm in communications
                ]
            
            self.log_action("data_gathered", f"Gathered context data: {list(context.keys())}")
            return context
            
        except Exception as e:
            self.log_action("error", f"Data gathering failed: {str(e)}")
            return {}
    
    async def _generate_response(self, user_input: str, intent: Dict, context: Dict, educator_id: int, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate intelligent response using Gemini with real context data"""
        self.state = AssistantState.THINKING
        
        # Create enhanced prompt with real data and recent conversation history
        history_block = ""
        if conversation_history:
            # Include up to last 10 messages to keep prompt short
            recent = conversation_history[-10:]
            lines = []
            for msg in recent:
                t = msg.get('type', 'user')
                content = msg.get('content', '')
                if t == 'user':
                    lines.append(f"User: {content}")
                else:
                    lines.append(f"Assistant: {content}")
            history_block = "\n".join(lines) + "\n\n"

        # Create enhanced prompt
        prompt = f"""
        {history_block}
        You are EduAssist AI, an intelligent educational administrative assistant.

        CONTEXT:
        - Teacher's request: "{user_input}"
        - Detected intent: {intent["intent"]}
        - Confidence: {intent["confidence"]}
        - Language: {self.language}
        - Autonomy mode: {self.autonomy_mode}

        AVAILABLE DATA:
        {self._format_context_for_prompt(context)}

        INSTRUCTIONS:
        1. Generate a natural, helpful response that directly addresses the teacher's request
        2. Use the real data provided to give specific, actionable information
        3. If the intent is clear and data is available, provide the requested information immediately
        4. Create specific actions that can be executed based on the request
        5. Consider the autonomy mode for approval requirements
        
        RESPONSE FORMAT (return only valid JSON):
        {{
            "message": "Natural, conversational response with specific information from the data",
            "data_summary": "Brief summary of relevant data if applicable",
            "actions": [
                {{
                    "type": "specific_action_name",
                    "description": "Clear description of what this action does",
                    "data": {{
                        "relevant_info": "specific data needed for action"
                    }},
                    "executable": true
                }}
            ],
            "requires_approval": false,
            "next_steps": ["Optional suggestions for follow-up actions"]
        }}
        
        INTENT-SPECIFIC GUIDANCE:
        
        For "list_students": Provide actual student names and sections from the data
        For "show_top_performers": List actual top students with their scores
        For "show_struggling_students": Identify students with low performance
        For "analyze_section_performance": Give specific section statistics
        For "send_communication": Prepare email content and recipient lists
        
        Always respond in {self.language} language preference.
        If no relevant data is available, explain what data is needed.
        
        Return only the JSON response, no other text.
        """
        
        try:
            response = await self._call_gemini(prompt)
            parsed_response = self._parse_json_response(response)
            
            # Enhance response with real data if available
            parsed_response = self._enhance_response_with_data(parsed_response, intent, context)
            
            return parsed_response
            
        except Exception as e:
            self.log_action("error", f"Response generation failed: {str(e)}")
            return self._create_fallback_response(intent, context)
    
    def _format_context_for_prompt(self, context: Dict) -> str:
        """Format context data for the prompt in a clean way"""
        formatted = []
        
        if "students" in context:
            student_count = len(context["students"])
            sections = set(s["section"] for s in context["students"])
            formatted.append(f"Students: {student_count} total across {len(sections)} sections ({', '.join(sections)})")
        
        if "grades" in context:
            grade_count = len(context["grades"])
            avg_score = sum(g["percentage"] for g in context["grades"] if g["percentage"]) / max(grade_count, 1)
            formatted.append(f"Grades: {grade_count} recent records, average score: {avg_score:.1f}%")
        
        if "attendance" in context:
            attendance_count = len(context["attendance"])
            present_count = sum(1 for a in context["attendance"] if a["present"])
            attendance_rate = (present_count / max(attendance_count, 1)) * 100
            formatted.append(f"Attendance: {attendance_count} records, {attendance_rate:.1f}% attendance rate")
        
        if "sections" in context:
            section_names = [s["name"] for s in context["sections"]]
            formatted.append(f"Sections: {', '.join(section_names)}")
        
        return "\n".join(formatted) if formatted else "No specific data available"
    
    def _enhance_response_with_data(self, response: Dict, intent: Dict, context: Dict) -> Dict:
        """Enhance response with actual data processing"""
        intent_name = intent["intent"]
        
        if intent_name == "list_students" and "students" in context:
            students = context["students"]
            response["data_summary"] = f"Found {len(students)} students across {len(set(s['section'] for s in students))} sections"
            response["actions"].append({
                "type": "display_student_list",
                "description": "Show complete student list",
                "data": {"students": students[:20]},  # Limit for display
                "executable": True
            })
        
        elif intent_name == "show_top_performers" and "grades" in context:
            # Calculate top performers
            student_scores = {}
            for grade in context["grades"]:
                student_id = grade["student_id"]
                if student_id not in student_scores:
                    student_scores[student_id] = {
                        "name": grade["student_name"],
                        "scores": [],
                        "total": 0
                    }
                if grade["percentage"]:
                    student_scores[student_id]["scores"].append(grade["percentage"])
            
            # Calculate averages
            for student_id in student_scores:
                scores = student_scores[student_id]["scores"]
                if scores:
                    student_scores[student_id]["average"] = sum(scores) / len(scores)
                else:
                    student_scores[student_id]["average"] = 0
            
            # Get top 5
            top_students = sorted(
                student_scores.items(),
                key=lambda x: x[1]["average"],
                reverse=True
            )[:5]
            
            top_list = [
                {"name": data["name"], "average": data["average"]}
                for _, data in top_students
            ]
            
            response["data_summary"] = f"Top {len(top_list)} performers identified"
            response["actions"].append({
                "type": "display_top_performers",
                "description": "Show top performing students",
                "data": {"top_students": top_list},
                "executable": True
            })
        
        elif intent_name == "show_struggling_students" and "grades" in context:
            # Find struggling students (below 60%)
            struggling = []
            student_scores = {}
            
            for grade in context["grades"]:
                student_id = grade["student_id"]
                if student_id not in student_scores:
                    student_scores[student_id] = {
                        "name": grade["student_name"],
                        "scores": []
                    }
                if grade["percentage"]:
                    student_scores[student_id]["scores"].append(grade["percentage"])
            
            for student_id, data in student_scores.items():
                if data["scores"]:
                    avg = sum(data["scores"]) / len(data["scores"])
                    if avg < 60:
                        struggling.append({"name": data["name"], "average": avg})
            
            response["data_summary"] = f"Found {len(struggling)} students who may need additional support"
            response["actions"].append({
                "type": "display_struggling_students",
                "description": "Show students needing support",
                "data": {"struggling_students": struggling},
                "executable": True
            })
        
        return response
    
    def _create_fallback_response(self, intent: Dict, context: Dict) -> Dict:
        """Create fallback response when Gemini fails"""
        intent_name = intent.get("intent", "unknown")
        
        responses = {
            "list_students": {
                "message": "I can help you view your student list. Let me gather that information.",
                "actions": [{"type": "fetch_students", "description": "Get student list", "data": {}, "executable": True}]
            },
            "show_grade_summary": {
                "message": "I'll get the grade summary for your students.",
                "actions": [{"type": "fetch_grades", "description": "Get grade information", "data": {}, "executable": True}]
            },
            "general_help": {
                "message": "I'm here to help with your administrative tasks. You can ask me to show students, analyze performance, send emails, or schedule meetings.",
                "actions": [{"type": "show_help", "description": "Show available commands", "data": {}, "executable": True}]
            }
        }
        
        default_response = {
            "message": "I understand you need assistance. Could you please clarify what you'd like me to help you with?",
            "actions": [],
            "requires_approval": False,
            "next_steps": ["Try asking 'show my students' or 'analyze performance'"]
        }
        
        return responses.get(intent_name, default_response)
    
    async def _execute_actions(self, actions: List[Dict], action_type: str, db: Session, educator_id: int) -> List[Dict]:
        """Execute actions based on autonomy mode"""
        executed = []
        
        for action in actions:
            should_execute = self._should_execute_action(action_type)
            
            if should_execute:
                self.state = AssistantState.ACTING
                result = await self._perform_action(action, db, educator_id)
                executed.append({
                    "action": action,
                    "result": result,
                    "executed": True,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                self.state = AssistantState.WAITING_APPROVAL
                executed.append({
                    "action": action,
                    "result": "waiting_approval",
                    "executed": False,
                    "timestamp": datetime.now().isoformat()
                })
        
        return executed
    
    def _should_execute_action(self, action_type: str) -> bool:
        """Determine if action should be executed based on autonomy mode"""
        # Normalize action_type to ActionType enum
        action_enum = None
        try:
            if isinstance(action_type, ActionType):
                action_enum = action_type
            else:
                action_enum = ActionType(action_type)
        except Exception:
            # Fallback: treat unknown as low risk
            action_enum = ActionType.LOW_RISK

        if self.autonomy_mode == AutonomyMode.MANUAL:
            return False
        elif self.autonomy_mode == AutonomyMode.ASSIST:
            return action_enum == ActionType.LOW_RISK
        elif self.autonomy_mode == AutonomyMode.AUTONOMOUS:
            return action_enum in [ActionType.LOW_RISK, ActionType.MEDIUM_RISK]
        return False
    
    async def _perform_action(self, action: Dict, db: Session, educator_id: int) -> str:
        """Perform the actual action"""
        action_type = action.get("type", "unknown")
        # Ensure action data resolves any high-level entities (e.g., section names -> student ids)
        try:
            data = action.get("data", {}) or {}
            data = await self._resolve_section_entities(data, db, educator_id)
            action["data"] = data
        except Exception as e:
            self.log_action("error", f"Failed to resolve action entities: {str(e)}")

        try:
            if action_type == "send_email":
                return await self._send_email(action.get("data", {}), db, educator_id)
            elif action_type == "schedule_meeting":
                return await self._schedule_meeting(action.get("data", {}), db, educator_id)
            elif action_type == "generate_report":
                return await self._generate_report(action.get("data", {}), db, educator_id)
            elif action_type == "update_calendar":
                return await self._update_calendar(action.get("data", {}), db, educator_id)
            else:
                return f"Action {action_type} executed successfully"
                
        except Exception as e:
            self.log_action("error", f"Action execution failed: {str(e)}")
            return f"Failed to execute {action_type}: {str(e)}"

    async def _resolve_section_entities(self, data: Dict, db: Session, educator_id: int) -> Dict:
        """Resolve higher-level entities in action data into concrete ids.

        - If data contains 'section' or 'section_name' (e.g. "Section A"), this will
          look up the corresponding Section owned by the educator and populate
          'section_id' and 'student_ids' in the data dict.
        - Safe no-op on failure to avoid blocking action flow.
        """
        try:
            if not data or not isinstance(data, dict):
                return data

            section_name = data.get("section") or data.get("section_name")
            if not section_name:
                return data

            # Lazy import to avoid circular imports at module load
            from app.models.student import Section, Student

            sname = str(section_name).strip()
            # Try case-insensitive match on section name
            section = db.query(Section).filter(Section.educator_id == educator_id, Section.name.ilike(sname)).first()

            if not section:
                # Try adding 'Section ' prefix if user said just 'A' or 'a'
                if not sname.lower().startswith("section"):
                    alt = f"Section {sname}"
                    section = db.query(Section).filter(Section.educator_id == educator_id, Section.name.ilike(alt)).first()

            if section:
                data["section_id"] = section.id
                students = db.query(Student).filter(Student.section_id == section.id).all()
                data["student_ids"] = [s.id for s in students]

            return data

        except Exception as e:
            # Don't raise — log and return original data so execution can continue
            self.log_action("error", f"_resolve_section_entities failed: {str(e)}")
            return data
    
    async def _send_email(self, data: Dict, db: Session, educator_id: int) -> str:
        """Send email / message action backed by the messaging models
        data can contain: receiver_id (single student), student_ids (list), receiver_type ('student'|'parent'|'both'),
        subject, message, is_report (bool)
        """
        try:
            from app.models.message import Message
            from app.models.report import SentReport, ReportType, RecipientType
            from app.models.notification import Notification, NotificationType
            from app.models.student import Student

            # Prepare common fields
            subject = data.get("subject", "Message from your teacher")
            message_text = data.get("message", "")
            is_report = data.get("is_report", False)
            receiver_type = data.get("receiver_type", "student")

            # Single student
            if data.get("receiver_id"):
                student = db.query(Student).filter(Student.id == int(data.get("receiver_id"))).first()
                if not student:
                    return "Recipient student not found"

                if is_report:
                    # Create SentReport
                    rec_enum = RecipientType.BOTH
                    if receiver_type == 'student':
                        rec_enum = RecipientType.STUDENT
                    elif receiver_type == 'parent':
                        rec_enum = RecipientType.PARENT

                    sent_report = SentReport(
                        report_type=ReportType.INDIVIDUAL_STUDENT,
                        title=subject,
                        description=message_text,
                        educator_id=educator_id,
                        student_id=student.id,
                        recipient_type=rec_enum,
                        report_data={"message": message_text}
                    )
                    db.add(sent_report)
                    db.commit()
                    db.refresh(sent_report)

                    # Create notification
                    try:
                        notification = Notification(
                            educator_id=educator_id,
                            student_id=student.id,
                            title=f"Report: {subject}",
                            message=message_text,
                            notification_type=NotificationType.GRADE_REPORT
                        )
                        db.add(notification)
                        db.commit()
                    except Exception:
                        db.rollback()

                    self.log_action("report_generated", f"Report created for student {student.id}")
                    return f"Report created (id={sent_report.id})"

                # Otherwise create a normal Message
                msg = Message(
                    sender_id=educator_id,
                    receiver_id=student.id,
                    receiver_type=receiver_type,
                    subject=subject,
                    message=message_text
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                # Create notification for parent/both
                try:
                    if receiver_type in ("parent", "both"):
                        notification = Notification(
                            educator_id=educator_id,
                            student_id=student.id,
                            title=subject,
                            message=message_text,
                            notification_type=NotificationType.COMMUNICATION
                        )
                        db.add(notification)
                        db.commit()
                except Exception:
                    db.rollback()

                self.log_action("email_sent", f"Message created to student {student.id}")
                return f"Message sent (id={msg.id})"

            # Bulk students list
            if data.get("student_ids"):
                student_ids = data.get("student_ids", [])
                created = 0
                for sid in student_ids:
                    student = db.query(Student).filter(Student.id == int(sid)).first()
                    if not student:
                        continue
                    if is_report:
                        sent_report = SentReport(
                            report_type=ReportType.INDIVIDUAL_STUDENT,
                            title=subject,
                            description=message_text,
                            educator_id=educator_id,
                            student_id=student.id,
                            recipient_type=RecipientType.BOTH,
                            report_data={"message": message_text}
                        )
                        db.add(sent_report)
                        db.commit()
                        db.refresh(sent_report)
                        try:
                            notification = Notification(
                                educator_id=educator_id,
                                student_id=student.id,
                                title=f"Report: {subject}",
                                message=message_text,
                                notification_type=NotificationType.GRADE_REPORT
                            )
                            db.add(notification)
                            db.commit()
                        except Exception:
                            db.rollback()
                        created += 1
                    else:
                        msg = Message(
                            sender_id=educator_id,
                            receiver_id=student.id,
                            receiver_type=receiver_type,
                            subject=subject,
                            message=message_text
                        )
                        db.add(msg)
                        db.commit()
                        db.refresh(msg)
                        created += 1

                self.log_action("bulk_message", f"Created {created} messages/reports")
                return f"Created {created} messages/reports"

            return "No valid recipient specified"
        except Exception as e:
            db.rollback()
            self.log_action("error", f"_send_email failed: {str(e)}")
            return f"Failed to send message: {str(e)}"
    
    async def _schedule_meeting(self, data: Dict, db: Session, educator_id: int) -> str:
        """Schedule meeting action by creating a Schedule record.
        Accepts ISO datetimes (start_datetime/end_datetime) or natural-language
        fields: 'datetime' (e.g. "Tomorrow at 10am") and 'duration' (e.g. "2 hours").
        """
        try:
            from app.models.schedule import Schedule, EventType, EventStatus

            title = data.get("title", "Meeting")
            description = data.get("description", "")
            start_raw = data.get("start_datetime") or data.get("datetime")
            end_raw = data.get("end_datetime")
            duration_raw = data.get("duration")
            location = data.get("location")

            if not start_raw:
                return "start_datetime (or 'datetime') required"

            import re

            def parse_nl_datetime(text: str) -> Optional[datetime]:
                if not text:
                    return None
                txt = str(text).lower()
                now = datetime.now()

                # Day selector
                base = now
                if "tomorrow" in txt:
                    base = now + timedelta(days=1)
                elif "day after" in txt or "day-after" in txt:
                    base = now + timedelta(days=2)
                elif "today" in txt:
                    base = now

                # Extract time component
                m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", txt)
                hour = 9
                minute = 0
                if m:
                    hour = int(m.group(1))
                    if m.group(2):
                        minute = int(m.group(2))
                    ampm = m.group(3)
                    if ampm:
                        if ampm == 'pm' and hour < 12:
                            hour += 12
                        if ampm == 'am' and hour == 12:
                            hour = 0

                try:
                    return datetime(base.year, base.month, base.day, hour, minute)
                except Exception:
                    return None

            def parse_duration_to_minutes(text: str) -> int:
                if not text:
                    return 60
                t = str(text).lower()
                m = re.search(r"(\d+)\s*(hour|hr|h)", t)
                if m:
                    return int(m.group(1)) * 60
                m2 = re.search(r"(\d+)\s*(minute|min|m)", t)
                if m2:
                    return int(m2.group(1))
                m3 = re.search(r"^(\d+)$", t.strip())
                if m3:
                    return int(m3.group(1))
                return 60

            # Parse start
            start_dt: Optional[datetime] = None
            if isinstance(start_raw, str) and re.match(r"\d{4}-\d{2}-\d{2}", start_raw):
                try:
                    start_dt = datetime.fromisoformat(start_raw.replace("Z", ""))
                except Exception:
                    start_dt = None
            if not start_dt:
                start_dt = parse_nl_datetime(start_raw)
            if not start_dt:
                return "Failed to parse 'datetime' into a valid start time"

            # Parse end
            end_dt: Optional[datetime] = None
            if end_raw:
                try:
                    if isinstance(end_raw, str) and re.match(r"\d{4}-\d{2}-\d{2}", end_raw):
                        end_dt = datetime.fromisoformat(end_raw.replace("Z", ""))
                    else:
                        end_dt = parse_nl_datetime(end_raw)
                except Exception:
                    end_dt = None

            if not end_dt:
                mins = parse_duration_to_minutes(duration_raw) if duration_raw else 60
                end_dt = start_dt + timedelta(minutes=mins)

            # Create schedule entry
            sched = Schedule(
                educator_id=educator_id,
                title=title,
                description=description,
                event_type=EventType.MEETING,
                start_datetime=start_dt,
                end_datetime=end_dt,
                location=location,
                status=EventStatus.SCHEDULED
            )
            db.add(sched)
            db.commit()
            db.refresh(sched)

            # Also create a Meeting record and per-recipient entries so students see it
            try:
                from app.models.meeting_schedule import Meeting, MeetingRecipient, RecipientType, DeliveryStatus
                from app.models.notification import Notification, NotificationType
                from app.models.message import Message
                from app.models.student import Student

                meeting = Meeting(
                    organizer_id=educator_id,
                    title=title,
                    description=description,
                    meeting_date=start_dt,
                    duration_minutes=int((end_dt - start_dt).total_seconds() // 60) if end_dt and start_dt else None,
                    location=location,
                    meeting_type=(data.get('meeting_type') or 'section'),
                    section_id=data.get('section_id'),
                    notify_parents=data.get('notify_parents', True),
                    requires_rsvp=data.get('requires_rsvp', False),
                    send_immediately=True
                )
                db.add(meeting)
                db.commit()
                db.refresh(meeting)

                student_ids = data.get('student_ids') or []
                created_recipients = 0
                for sid in student_ids:
                    try:
                        student = db.query(Student).filter(Student.id == int(sid)).first()
                        if not student:
                            continue

                        recipient = MeetingRecipient(
                            meeting_id=meeting.id,
                            recipient_id=student.id,
                            recipient_type=RecipientType.STUDENT,
                            delivery_status=DeliveryStatus.SENT,
                            delivery_methods=["in_app"]
                        )
                        db.add(recipient)
                        db.commit()
                        db.refresh(recipient)
                        created_recipients += 1

                        # Create in-app notification for the student
                        try:
                            note = Notification(
                                educator_id=educator_id,
                                student_id=student.id,
                                title=f"Meeting: {title}",
                                message=f"{description or 'Meeting scheduled'}\nWhen: {start_dt.isoformat()}\nLocation: {location or 'TBA'}",
                                notification_type=NotificationType.REMINDER
                            )
                            db.add(note)
                            db.commit()
                        except Exception:
                            db.rollback()

                        # Create a Message entry so it appears under student's messages as well
                        try:
                            msg = Message(
                                sender_id=educator_id,
                                receiver_id=student.id,
                                receiver_type='student',
                                subject=f"Meeting: {title}",
                                message=f"{description or ''}\nWhen: {start_dt.isoformat()}\nLocation: {location or 'TBA'}"
                            )
                            db.add(msg)
                            db.commit()
                        except Exception:
                            db.rollback()

                    except Exception:
                        db.rollback()

                self.log_action("meeting_scheduled", f"Meeting scheduled id={sched.id}; meeting_record={meeting.id}; recipients={created_recipients}")

                # If a calendar email was provided, attempt to create the schedule on that educator's calendar
                calendar_email = data.get('calendar') or data.get('calendar_email')
                calendar_msg = None
                if calendar_email:
                    try:
                        from app.models.educator import Educator
                        cal_owner = db.query(Educator).filter(Educator.email == calendar_email).first()
                        if cal_owner:
                            upd = {
                                "action": "create",
                                "title": title,
                                "description": description,
                                "start_datetime": start_dt.isoformat() if start_dt else None,
                                "end_datetime": end_dt.isoformat() if end_dt else None,
                                "location": location,
                            }
                            try:
                                # Create the schedule on the target educator's calendar
                                await self._update_calendar(upd, db, cal_owner.id)
                                self.log_action("calendar_forwarded", f"Created schedule on calendar {calendar_email} for meeting id={meeting.id}")
                                calendar_msg = f"Created event on calendar {calendar_email} (educator_id={cal_owner.id})"
                            except Exception as e:
                                self.log_action("error", f"Failed to create event on {calendar_email}: {e}")
                                calendar_msg = f"Failed to create event on {calendar_email}: {e}"
                        else:
                            self.log_action("calendar_not_found", f"Calendar owner not found for {calendar_email}")
                            calendar_msg = f"Calendar owner not found for {calendar_email}"
                    except Exception as e:
                        self.log_action("error", f"calendar handling failed: {e}")
                        calendar_msg = f"calendar handling failed: {e}"

                # Build a clearer return message for the caller
                if calendar_msg:
                    return f"Meeting scheduled (id={sched.id}); {calendar_msg}"
                else:
                    return f"Meeting scheduled (id={sched.id})"
            except Exception as e:
                # Non-fatal: log and continue
                self.log_action("error", f"Failed to create meeting recipients/notifications: {str(e)}")

            return f"Meeting scheduled (id={sched.id})"
        except Exception as e:
            db.rollback()
            self.log_action("error", f"_schedule_meeting failed: {str(e)}")
            return f"Failed to schedule meeting: {str(e)}"
    
    async def _generate_report(self, data: Dict, db: Session, educator_id: int) -> str:
        """Generate and persist a SentReport record
        data can include: type (performance_report/attendance_report), student_id, section_id, title, description, report_data
        """
        try:
            from app.models.report import SentReport, ReportType, RecipientType
            from app.models.notification import Notification, NotificationType

            report_type_raw = data.get("type", "performance_report")
            title = data.get("title", "Report")
            description = data.get("description", "")
            report_data = data.get("report_data", {})

            # Map report type
            if report_type_raw == "performance_report":
                report_type = ReportType.INDIVIDUAL_STUDENT
            elif report_type_raw == "attendance_report":
                report_type = ReportType.INDIVIDUAL_STUDENT
            else:
                report_type = ReportType.INDIVIDUAL_STUDENT

            # Create SentReport
            sent_report = SentReport(
                report_type=report_type,
                title=title,
                description=description,
                educator_id=educator_id,
                student_id=data.get("student_id"),
                section_id=data.get("section_id"),
                recipient_type=RecipientType.BOTH,
                report_data=report_data
            )
            db.add(sent_report)
            db.commit()
            db.refresh(sent_report)

            # Create notifications where applicable
            try:
                if sent_report.student_id:
                    notification = Notification(
                        educator_id=educator_id,
                        student_id=sent_report.student_id,
                        title=f"Report: {title}",
                        message=description or "Your teacher has sent a report.",
                        notification_type=NotificationType.GRADE_REPORT
                    )
                    db.add(notification)
                    db.commit()
            except Exception:
                db.rollback()

            self.log_action("report_generated", f"Report created id={sent_report.id}")
            return f"Report created (id={sent_report.id})"
        except Exception as e:
            db.rollback()
            self.log_action("error", f"_generate_report failed: {str(e)}")
            return f"Failed to generate report: {str(e)}"
    
    async def _update_calendar(self, data: Dict, db: Session, educator_id: int) -> str:
        """Update calendar by creating or updating Schedule entries
        data may include: id (to update), title, start_datetime, end_datetime, location, action ('create'|'update'|'delete')
        """
        try:
            from app.models.schedule import Schedule, EventType, EventStatus

            action = data.get("action", "create")
            if action == "delete" and data.get("id"):
                sched = db.query(Schedule).filter(Schedule.id == int(data.get("id")), Schedule.educator_id == educator_id).first()
                if not sched:
                    return "Schedule not found"
                db.delete(sched)
                db.commit()
                self.log_action("calendar_updated", f"Schedule deleted id={data.get('id')}")
                return f"Schedule deleted (id={data.get('id')})"

            # create or update
            start_iso = data.get("start_datetime")
            end_iso = data.get("end_datetime")
            title = data.get("title", "Event")
            description = data.get("description", "")
            location = data.get("location")

            start_dt = datetime.fromisoformat(start_iso.replace("Z", "")) if start_iso else None
            end_dt = datetime.fromisoformat(end_iso.replace("Z", "")) if end_iso else (start_dt + timedelta(hours=1) if start_dt else None)

            if data.get("id"):
                sched = db.query(Schedule).filter(Schedule.id == int(data.get("id")), Schedule.educator_id == educator_id).first()
                if not sched:
                    return "Schedule not found"
                if title:
                    sched.title = title
                if description:
                    sched.description = description
                if start_dt:
                    sched.start_datetime = start_dt
                if end_dt:
                    sched.end_datetime = end_dt
                if location:
                    sched.location = location
                db.commit()
                db.refresh(sched)
                self.log_action("calendar_updated", f"Schedule updated id={sched.id}")
                return f"Schedule updated (id={sched.id})"

            # create new schedule
            from app.models.schedule import Schedule as ScheduleModel, EventType as EType, EventStatus as EStatus
            sched = ScheduleModel(
                educator_id=educator_id,
                title=title,
                description=description,
                event_type=EType.OTHER,
                start_datetime=start_dt,
                end_datetime=end_dt,
                location=location,
                status=EStatus.SCHEDULED
            )
            db.add(sched)
            db.commit()
            db.refresh(sched)
            self.log_action("calendar_updated", f"Schedule created id={sched.id}")
            return f"Schedule created (id={sched.id})"
        except Exception as e:
            db.rollback()
            self.log_action("error", f"_update_calendar failed: {str(e)}")
            return f"Failed to update calendar: {str(e)}"
    
    def _enhance_intent_data(self, intent_data: Dict, user_input: str) -> Dict[str, Any]:
        """Enhance and validate intent analysis results"""
        # Ensure all required fields exist
        enhanced = {
            "intent": intent_data.get("intent", "unknown"),
            "action_type": intent_data.get("action_type", "low_risk"),
            "entities": intent_data.get("entities", {}),
            "confidence": min(intent_data.get("confidence", 0.5), 1.0),
            "requires_data": intent_data.get("requires_data", []),
            "suggested_actions": intent_data.get("suggested_actions", []),
            "natural_response": intent_data.get("natural_response", "I'll help you with that!")
        }
        
        # Enhance entities based on pattern matching
        enhanced["entities"] = self._extract_additional_entities(user_input, enhanced["entities"])
        
        # Determine data requirements based on intent
        enhanced["requires_data"] = self._determine_data_requirements(enhanced["intent"])
        
        return enhanced
    
    def _extract_additional_entities(self, user_input: str, existing_entities: Dict) -> Dict:
        """Extract additional entities using pattern matching"""
        import re
        
        enhanced = existing_entities.copy()
        
        # Section patterns
        section_patterns = [
            r"section\s+([a-zA-Z])",
            r"class\s+([a-zA-Z])",
            r"విభాగం\s+([a-zA-Z])",  # Telugu for section
        ]
        for pattern in section_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match and not enhanced.get("section"):
                enhanced["section"] = f"Section {match.group(1).upper()}"
        
        # Subject patterns
        subjects = ["math", "science", "english", "physics", "chemistry", "biology", "history"]
        for subject in subjects:
            if subject in user_input.lower() and not enhanced.get("subject"):
                enhanced["subject"] = subject.title()
        
        # Number patterns
        number_patterns = [
            r"top\s+(\d+)",
            r"best\s+(\d+)",
            r"(\d+)\s+students",
            r"below\s+(\d+)",
        ]
        for pattern in number_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match and not enhanced.get("number"):
                enhanced["number"] = int(match.group(1))
        
        # Time frame patterns
        time_patterns = [
            r"this\s+(week|month|term)",
            r"last\s+(week|month|term)",
            r"(today|yesterday|tomorrow)",
            r"(october|november|december)",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match and not enhanced.get("time_frame"):
                enhanced["time_frame"] = match.group(1).lower()
        
        return enhanced
    
    def _determine_data_requirements(self, intent: str) -> List[str]:
        """Determine what data is needed based on intent"""
        data_map = {
            "list_students": ["students", "sections"],
            "show_top_performers": ["students", "grades", "sections"],
            "show_struggling_students": ["students", "grades", "sections"],
            "show_attendance_issues": ["students", "attendance", "sections"],
            "analyze_section_performance": ["students", "grades", "sections"],
            "show_grade_summary": ["grades", "subjects", "sections"],
            "compare_section_performance": ["grades", "sections", "students"],
            "analyze_subject_performance": ["grades", "subjects", "students"],
            "send_communication": ["students", "communications"],
            "send_reminder": ["students", "communications"],
            "send_appreciation": ["students", "grades", "communications"],
            "schedule_meeting": ["calendar", "students"],
            "show_schedule": ["calendar"],
            "check_availability": ["calendar"],
            "generate_report": ["students", "grades", "attendance"],
            "attendance_report": ["students", "attendance"],
            "performance_report": ["students", "grades", "subjects"],
        }
        
        return data_map.get(intent, ["students"])
    
    def _fallback_intent_analysis(self, user_input: str) -> Dict[str, Any]:
        """Fallback intent analysis when Gemini fails"""
        user_lower = user_input.lower()
        
        # Simple keyword-based intent detection
        if any(word in user_lower for word in ["show", "list", "get", "చూపించు"]):
            if any(word in user_lower for word in ["student", "విద్యార్థి"]):
                return {
                    "intent": "list_students",
                    "action_type": "low_risk",
                    "entities": {},
                    "confidence": 0.7,
                    "requires_data": ["students", "sections"],
                    "suggested_actions": ["show_student_list"],
                    "natural_response": "I'll show you the student list right away!"
                }
            elif any(word in user_lower for word in ["grade", "marks", "గ్రేడ్"]):
                return {
                    "intent": "show_grade_summary", 
                    "action_type": "low_risk",
                    "entities": {},
                    "confidence": 0.7,
                    "requires_data": ["grades", "students"],
                    "suggested_actions": ["show_grades"],
                    "natural_response": "Let me get the grade information for you!"
                }
        
        if any(word in user_lower for word in ["send", "email", "పంపించు"]):
            return {
                "intent": "send_communication",
                "action_type": "medium_risk", 
                "entities": {},
                "confidence": 0.6,
                "requires_data": ["students", "communications"],
                "suggested_actions": ["prepare_email"],
                "natural_response": "I can help you send an email. What would you like to communicate?"
            }
        
        # Default fallback
        return {
            "intent": "general_help",
            "action_type": "low_risk",
            "entities": {},
            "confidence": 0.3,
            "requires_data": [],
            "suggested_actions": ["show_help"],
            "natural_response": "I'm here to help! Could you please clarify what you'd like me to do?"
        }
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            # Use response tuning parameters from settings to reduce latency and control output size
            max_tokens = getattr(settings, 'GEMINI_MAX_TOKENS', 256)
            temperature = getattr(settings, 'GEMINI_TEMPERATURE', 0.2)
            # Call the model with explicit generation params where supported
            try:
                response = self.model.generate_content(prompt, max_output_tokens=max_tokens, temperature=temperature)
            except TypeError:
                # Fallback if client library expects different kw names
                response = self.model.generate_content(prompt)

            # Extract text if present, otherwise string-convert
            text = getattr(response, 'text', None)
            if text is None:
                return str(response)
            return text
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Gemini"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            return {
                "message": response,
                "actions": [],
                "requires_approval": False,
                "next_steps": []
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current assistant status"""
        return {
            "state": self.state,
            "autonomy_mode": self.autonomy_mode,
            "language": self.language,
            "capabilities": [
                "Administrative task automation",
                "Email composition and sending",
                "Calendar management",
                "Student performance analysis",
                "Report generation",
                "Multilingual support (English/Telugu)",
                "Background task processing"
            ],
            "recent_actions": self.action_log[-10:],
            "version": "2.0.0"
        }

# Global assistant instance
gemini_assistant = GeminiEducatorAssistant()