#!/usr/bin/env python3
"""
Password reset script for educator AI assistant database
"""
import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """Hash password using sha256"""
    return hashlib.sha256(password.encode()).hexdigest()

def reset_user_password():
    try:
        # Connect to database
        conn = sqlite3.connect('educator_assistant.db')
        cursor = conn.cursor()
        
        # Check all users and their communication counts
        print("📋 Current Users and Communication Stats:")
        cursor.execute("""
            SELECT u.email, u.first_name, u.last_name,
                   (SELECT COUNT(*) FROM communications WHERE sender_email = u.email) as sent_count,
                   (SELECT COUNT(*) FROM communications WHERE recipient_email = u.email) as received_count
            FROM educators u
            ORDER BY u.email
        """)
        
        users = cursor.fetchall()
        for user in users:
            email, first_name, last_name, sent, received = user
            full_name = f"{first_name} {last_name}" if first_name and last_name else email.split('@')[0]
            print(f"  👤 {email} ({full_name})")
            print(f"     📤 Sent: {sent} emails | 📥 Received: {received} emails")
            print()
        
        # Reset password for shaafiya07@gmail.com
        new_password = "password123"
        hashed_password = hash_password(new_password)
        
        cursor.execute("""
            UPDATE educators 
            SET hashed_password = ? 
            WHERE email = ?
        """, (hashed_password, "shaafiya07@gmail.com"))
        
        if cursor.rowcount > 0:
            print("✅ Password reset successful!")
            print(f"📧 Email: shaafiya07@gmail.com")
            print(f"🔑 New Password: {new_password}")
            print()
            print("💡 This user has emails to display - perfect for testing!")
        else:
            print("❌ User shaafiya07@gmail.com not found!")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")

if __name__ == "__main__":
    reset_user_password()