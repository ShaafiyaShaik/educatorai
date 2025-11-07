import sqlite3

# Connect to the database
conn = sqlite3.connect('educator_assistant.db')
cursor = conn.cursor()

# Check if educators table exists and has any data
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:", tables)

try:
    cursor.execute("SELECT id, email, first_name, last_name FROM educators;")
    educators = cursor.fetchall()
    print(f"\nEducators in database ({len(educators)} total):")
    for educator in educators:
        print(f"  ID: {educator[0]}, Email: {educator[1]}, Name: {educator[2]} {educator[3]}")
except Exception as e:
    print("Error querying educators table:", e)

conn.close()