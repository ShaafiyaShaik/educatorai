import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🗄️ Creating meeting scheduling tables...")

# Create meetings table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organizer_id INTEGER NOT NULL REFERENCES educators(id),
        title VARCHAR(200) NOT NULL,
        description TEXT,
        meeting_date TIMESTAMP,
        duration_minutes INTEGER DEFAULT 60,
        location VARCHAR(200),
        virtual_meeting_link VARCHAR(500),
        meeting_type VARCHAR(20) NOT NULL,
        section_id INTEGER REFERENCES sections(id),
        notify_parents BOOLEAN DEFAULT 1,
        requires_rsvp BOOLEAN DEFAULT 0,
        send_reminders BOOLEAN DEFAULT 1,
        reminder_minutes_before INTEGER DEFAULT 60,
        send_immediately BOOLEAN DEFAULT 1,
        scheduled_send_at TIMESTAMP,
        attachments TEXT DEFAULT '[]',
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        sent_at TIMESTAMP
    )
""")

# Create meeting_recipients table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS meeting_recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
        recipient_id INTEGER NOT NULL,
        recipient_type VARCHAR(20) NOT NULL,
        delivery_status VARCHAR(20) DEFAULT 'pending',
        rsvp_status VARCHAR(20) DEFAULT 'no_response',
        delivery_methods TEXT DEFAULT '["in_app"]',
        sent_at TIMESTAMP,
        delivered_at TIMESTAMP,
        read_at TIMESTAMP,
        rsvp_at TIMESTAMP,
        rsvp_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )
""")

# Create indexes for performance
cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_organizer ON meetings(organizer_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_section ON meetings(section_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(meeting_date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_recipients_meeting ON meeting_recipients(meeting_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_recipients_recipient ON meeting_recipients(recipient_id, recipient_type)")

conn.commit()
conn.close()

print("✅ Meeting scheduling tables created successfully!")