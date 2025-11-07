"""
Communication Agent using template-based approach with optional Hugging Face enhancement
"""

from typing import Optional, List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


class SimpleTextGenerator:
    """Simple text generator with predefined templates and basic AI enhancement"""
    
    def __init__(self):
        self.use_ai = settings.USE_LOCAL_AI
        self.hf_pipeline = None
        if self.use_ai:
            self._try_initialize_ai()
    
    def _try_initialize_ai(self):
        """Try to initialize Hugging Face AI (graceful fallback if not available)"""
        # Skip AI initialization on startup to avoid large downloads
        # Users can enable USE_LOCAL_AI=True in config if they want AI features
        if not self.use_ai:
            print("🤖 AI disabled in config - using template responses")
            return
            
        try:
            from transformers import pipeline
            import torch
            print("⏳ Initializing AI model (this may take a few minutes on first run)...")
            self.hf_pipeline = pipeline(
                "text-generation",
                model="gpt2",  # Smaller, faster model
                max_length=150,
                do_sample=True,
                temperature=0.7,
                pad_token_id=50256
            )
            print("✅ Hugging Face AI initialized successfully")
        except Exception as e:
            print(f"⚠️ AI initialization failed, using templates: {e}")
            self.hf_pipeline = None
    
    def generate_text(self, prompt: str, max_length: int = 150) -> str:
        """Generate text using AI or templates"""
        if self.hf_pipeline:
            try:
                response = self.hf_pipeline(prompt, max_length=max_length, do_sample=True)
                return response[0]['generated_text'][len(prompt):].strip()
            except Exception as e:
                print(f"AI generation failed, using template: {e}")
        
        return self._template_response(prompt)
    
    def _template_response(self, prompt: str) -> str:
        """Template-based response system"""
        prompt_lower = prompt.lower()
        
        if "email" in prompt_lower:
            if "meeting" in prompt_lower:
                return "This email is to confirm our upcoming meeting. Please let me know if you need any adjustments to the schedule."
            elif "reminder" in prompt_lower:
                return "This is a friendly reminder about your upcoming commitment. Please ensure you are prepared."
            elif "notification" in prompt_lower:
                return "This notification contains important information that requires your attention."
            else:
                return "Thank you for your message. This email contains the information you requested."
        
        elif "reminder" in prompt_lower:
            return "This is an automated reminder about your scheduled item. Please review the details and prepare accordingly."
        
        elif "notification" in prompt_lower:
            return "This notification contains important updates. Please review the information provided."
        
        else:
            return "This is an automated message from the university administrative system. Thank you for your attention."


class CommunicationAgent:
    """AI-enhanced Communication Agent with fallback to templates"""

    def __init__(self):
        self.text_generator = SimpleTextGenerator()
        print(f"🤖 Communication Agent initialized (AI: {'✅' if self.text_generator.hf_pipeline else '❌ Templates only'})")

    def send_automated_email(self, recipient: str, email_type: str, context: Dict[str, Any]) -> str:
        """Send automated email with AI-enhanced or template-based content"""
        try:
            # Generate email content
            prompt = f"Write a professional {email_type} email about {context.get('subject', 'university matter')}"
            ai_content = self.text_generator.generate_text(prompt, max_length=200)
            
            # Enhanced email templates
            templates = {
                "notification": {
                    "subject": f"📧 Notification: {context.get('subject', 'Important Update')}",
                    "content": f"""
Dear Recipient,

{ai_content}

Subject: {context.get('subject', 'Important Update')}
Details: {context.get('content', 'Please see the attached information.')}

Best regards,
{context.get('sender', 'University Administration')}
{context.get('department', 'Academic Affairs')}
                    """.strip()
                },
                "reminder": {
                    "subject": f"⏰ Reminder: {context.get('subject', 'Upcoming Event')}",
                    "content": f"""
Dear Recipient,

{ai_content}

Event: {context.get('subject', 'Upcoming commitment')}
Details: {context.get('content', 'Please review your schedule.')}

Thank you for your attention.

Best regards,
{context.get('sender', 'University Administration')}
                    """.strip()
                },
                "meeting": {
                    "subject": f"🤝 Meeting: {context.get('subject', 'Scheduled Meeting')}",
                    "content": f"""
Dear Recipient,

{ai_content}

Meeting Topic: {context.get('subject', 'Discussion')}
Details: {context.get('content', 'Meeting details will be provided.')}

Please confirm your attendance.

Best regards,
{context.get('sender', 'University Administration')}
                    """.strip()
                }
            }
            
            template = templates.get(email_type, templates["notification"])
            
            # Simulate email sending (or actually send if SMTP configured)
            if settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD:
                msg = MIMEMultipart()
                msg['From'] = settings.EMAIL_USERNAME
                msg['To'] = recipient
                msg['Subject'] = template["subject"]
                msg.attach(MIMEText(template["content"], 'plain'))
                
                try:
                    server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                    server.starttls()
                    server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                    server.sendmail(settings.EMAIL_USERNAME, recipient, msg.as_string())
                    server.quit()
                    return f"✅ Email sent successfully to {recipient}"
                except Exception as e:
                    return f"⚠️ Email sending failed: {e}, but content generated: {template['subject']}"
            else:
                return f"📧 Email prepared for {recipient}: {template['subject']} (SMTP not configured)"
                
        except Exception as e:
            return f"❌ Error in communication agent: {str(e)}"

    def create_bulk_notification(self, recipients: List[str], notification_type: str, details: str) -> str:
        """Create bulk notifications"""
        try:
            results = []
            context = {"subject": details, "content": details, "sender": "University Administration"}
            
            for recipient in recipients[:5]:  # Limit to 5 for demo
                result = self.send_automated_email(recipient, notification_type, context)
                results.append(f"  • {recipient}: {result}")
            
            return f"📨 Bulk notification sent to {len(recipients)} recipients:\n" + "\n".join(results)
            
        except Exception as e:
            return f"❌ Error creating bulk notification: {str(e)}"

    def generate_communication_template(self, communication_type: str, variables: Dict[str, Any]) -> str:
        """Generate communication template"""
        try:
            # AI-enhanced templates
            prompt = f"Create a professional {communication_type} template"
            ai_enhancement = self.text_generator.generate_text(prompt, max_length=100)
            
            enhanced_templates = {
                "meeting_reminder": f"""
Subject: 🤝 Meeting Reminder: {{meeting_title}}

Dear {{recipient_name}},

{ai_enhancement}

Meeting Details:
- Title: {{meeting_title}}
- Date & Time: {{date_time}}
- Location: {{location}}
- Duration: {{duration}}

Please confirm your attendance and prepare any necessary materials.

Best regards,
{{sender_name}}
{{department}}
                """.strip(),
                
                "class_cancellation": f"""
Subject: ⚠️ Class Cancellation - {{course_code}}

Dear Students,

{ai_enhancement}

Due to {{reason}}, the {{course_code}} class scheduled for {{date_time}} has been cancelled.

Alternative arrangements:
- Makeup session: {{makeup_date}}
- Materials: {{materials_info}}

We apologize for any inconvenience.

Best regards,
{{instructor_name}}
                """.strip(),
                
                "grade_notification": f"""
Subject: 📊 Grade Update - {{assignment_name}}

Dear {{student_name}},

{ai_enhancement}

Grade Information:
- Assignment: {{assignment_name}}
- Grade: {{grade}}
- Comments: {{comments}}
- Posted Date: {{date_posted}}

For questions, please visit my office hours.

Best regards,
{{instructor_name}}
                """.strip()
            }
            
            return enhanced_templates.get(communication_type, f"Template for {communication_type}:\n{ai_enhancement}")
            
        except Exception as e:
            return f"❌ Error generating template: {str(e)}"


# Global communication agent instance
communication_agent = CommunicationAgent()
