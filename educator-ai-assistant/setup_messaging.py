#!/usr/bin/env python3
"""
Database migration to add messaging tables
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.database import get_db, engine
from app.models.message import Message, MessageTemplate
from app.core.database import Base

def create_messaging_tables():
    """Create messaging tables in the database"""
    try:
        print("🔄 Creating messaging tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Messaging tables created successfully!")
        
        # Verify tables exist
        db = next(get_db())
        try:
            # Test message table
            message_count = db.query(Message).count()
            print(f"📧 Messages table: {message_count} records")
            
            # Test template table  
            template_count = db.query(MessageTemplate).count()
            print(f"📝 Message templates table: {template_count} records")
            
        except Exception as e:
            print(f"⚠️  Table verification warning: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating messaging tables: {e}")
        return False
    
    return True

def create_sample_templates():
    """Create sample message templates"""
    db = next(get_db())
    
    try:
        # Check if templates already exist
        existing_count = db.query(MessageTemplate).count()
        if existing_count > 0:
            print(f"📝 {existing_count} templates already exist, skipping sample creation")
            return
        
        print("🔄 Creating sample message templates...")
        
        sample_templates = [
            {
                "educator_id": 4,  # shaaf@gmail.com
                "template_name": "Assignment Reminder",
                "subject_template": "Assignment Due: [Subject Name]",
                "message_template": "Dear student,\n\nThis is a friendly reminder that your assignment for [Subject Name] is due on [Due Date]. Please make sure to submit your work on time.\n\nIf you have any questions or need help, please don't hesitate to reach out.\n\nBest regards,\nYour Teacher",
                "message_type": "academic"
            },
            {
                "educator_id": 4,
                "template_name": "Excellent Performance",
                "subject_template": "Great Work!",
                "message_template": "Dear student,\n\nI wanted to take a moment to recognize your excellent performance in class. Your dedication and hard work are truly paying off!\n\nKeep up the fantastic work!\n\nBest regards,\nYour Teacher",
                "message_type": "academic"
            },
            {
                "educator_id": 4,
                "template_name": "Attendance Concern",
                "subject_template": "Attendance Reminder",
                "message_template": "Dear student,\n\nI've noticed that you've missed several classes recently. Regular attendance is important for your academic success.\n\nPlease let me know if there are any issues I can help you with.\n\nBest regards,\nYour Teacher",
                "message_type": "attendance"
            },
            {
                "educator_id": 4,
                "template_name": "Positive Behavior",
                "subject_template": "Thank You!",
                "message_template": "Dear student,\n\nI wanted to thank you for your positive attitude and behavior in class. You're setting a great example for your classmates!\n\nYour participation and enthusiasm make the learning environment better for everyone.\n\nBest regards,\nYour Teacher",
                "message_type": "behavioral"
            }
        ]
        
        for template_data in sample_templates:
            template = MessageTemplate(**template_data)
            db.add(template)
        
        db.commit()
        print(f"✅ Created {len(sample_templates)} sample templates")
        
    except Exception as e:
        print(f"❌ Error creating sample templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting messaging system setup...")
    
    if create_messaging_tables():
        create_sample_templates()
        print("✨ Messaging system setup completed!")
    else:
        print("❌ Messaging system setup failed!")
        sys.exit(1)