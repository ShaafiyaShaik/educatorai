#!/usr/bin/env python3
"""
Quick script to check Communication table records
"""
import sqlite3
import json
from datetime import datetime

def check_communications():
    try:
        # Connect to the database
        conn = sqlite3.connect('educator_db.sqlite')
        cursor = conn.cursor()
        
        # Check table structure first
        cursor.execute("PRAGMA table_info(Communications)")
        columns = cursor.fetchall()
        print("Communications table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check Communications table
        cursor.execute("SELECT COUNT(*) FROM Communications")
        comm_count = cursor.fetchone()[0]
        print(f"\nTotal Communication records: {comm_count}")
        
        if comm_count > 0:
            cursor.execute("SELECT id, subject, sender_email, recipient_email, email_type, sent_at FROM Communications ORDER BY sent_at DESC LIMIT 5")
            comms = cursor.fetchall()
            print("\nRecent Communications (first 5):")
            for comm in comms:
                print(f"  ID: {comm[0]}, Subject: {comm[1]}, From: {comm[2]}, To: {comm[3]}, Type: {comm[4]}, Sent: {comm[5]}")
        
        # Check Notifications table structure
        cursor.execute("PRAGMA table_info(Notifications)")
        columns = cursor.fetchall()
        print("\nNotifications table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check Notifications table
        cursor.execute("SELECT COUNT(*) FROM Notifications")
        notif_count = cursor.fetchone()[0]
        print(f"\nTotal Notification records: {notif_count}")
        
        if notif_count > 0:
            cursor.execute("SELECT id, title, additional_data FROM Notifications WHERE additional_data IS NOT NULL ORDER BY created_at DESC LIMIT 3")
            notifs = cursor.fetchall()
            print("\nNotifications with structured data:")
            for notif in notifs:
                print(f"ID: {notif[0]}")
                print(f"Title: {notif[1]}")
                print(f"Additional Data: {notif[2]}")
                print("---")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_communications()