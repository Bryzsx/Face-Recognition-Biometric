import sqlite3

conn = sqlite3.connect("biometric.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS employee (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    id_number TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS facial_data (
    face_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    face_encoding BLOB,
    FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    date TEXT,
    morning_in TEXT,
    attendance_status TEXT,
    verification_method TEXT
)
""")

conn.commit()
conn.close()
print("✅ Database ready")
