#!/usr/bin/env python3
"""
Clean up duplicate Communication records to prevent duplicate notifications
"""
import sqlite3
from datetime import datetime

def clean_communication_duplicates():
    try:
        # Connect to the database
        conn = sqlite3.connect('educator_db.sqlite')
        cursor = conn.cursor()
        
        # Show current counts
        cursor.execute("SELECT COUNT(*) FROM Communications")
        comm_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Notifications")
        notif_count = cursor.fetchone()[0]
        print(f"Before cleanup: {comm_count} Communications, {notif_count} Notifications")
        
        # Delete all Communication records to prevent duplicates
        # Since we're now using Notifications table exclusively
        cursor.execute("DELETE FROM Communications")
        deleted_count = cursor.rowcount
        
        # Commit the changes
        conn.commit()
        
        # Show final counts
        cursor.execute("SELECT COUNT(*) FROM Communications")
        comm_count_after = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Notifications")
        notif_count_after = cursor.fetchone()[0]
        
        print(f"After cleanup: {comm_count_after} Communications, {notif_count_after} Notifications")
        print(f"Deleted {deleted_count} Communication records")
        
        conn.close()
        print("✅ Cleanup completed successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_communication_duplicates()