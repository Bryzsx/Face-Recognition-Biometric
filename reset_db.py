import sqlite3

DB = "biometric.db"

conn = sqlite3.connect(DB)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employee (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    employee_code TEXT UNIQUE NOT NULL,
    department TEXT,
    position TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    date TEXT,
    morning_in TEXT,
    lunch_out TEXT,
    afternoon_in TEXT,
    time_out TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS facial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER UNIQUE,
    face_encoding BLOB
)
""")

conn.commit()
conn.close()

print("✅ Database reset & tables created successfully")
