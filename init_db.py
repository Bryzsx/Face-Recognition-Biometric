import sqlite3

DB_NAME = "biometric.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# ADMIN TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL
)
""")

# EMPLOYEES TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    employee_code TEXT,
    department TEXT,
    position TEXT,
    status TEXT DEFAULT 'Active'
)
""")

# ATTENDANCE TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    date TEXT,
    morning_in TEXT,
    attendance_status TEXT,
    verification_method TEXT,
    FOREIGN KEY(employee_id) REFERENCES employees(id)
)
""")

# DEFAULT ADMIN
cur.execute("""
INSERT OR IGNORE INTO admin (username, password, name)
VALUES ('admin', 'admin123', 'System Admin')
""")

conn.commit()
conn.close()

print("✅ Database initialized successfully")
