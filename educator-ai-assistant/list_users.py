import sqlite3

def list_all_users():
    """List all users in the database"""
    
    conn = sqlite3.connect("educator_assistant.db")
    cursor = conn.cursor()
    
    print("👥 All users in database:")
    cursor.execute("SELECT id, email, first_name, last_name, is_active FROM educators")
    users = cursor.fetchall()
    
    if not users:
        print("❌ No users found!")
        return []
    
    for user in users:
        status = "✅ Active" if user[4] else "❌ Inactive"
        print(f"  ID: {user[0]} | Email: {user[1]} | Name: {user[2]} {user[3]} | {status}")
    
    conn.close()
    return [user[1] for user in users]  # Return emails

if __name__ == "__main__":
    emails = list_all_users()
    
    if emails:
        print(f"\n🔍 Found {len(emails)} users")
        print("💡 Try logging in with any of these emails:")
        for email in emails:
            if "test" in email.lower():
                print(f"  📧 {email} (password: test123)")
            else:
                print(f"  📧 {email} (password: password123)")
    else:
        print("\n❌ No users found. Database might be empty.")