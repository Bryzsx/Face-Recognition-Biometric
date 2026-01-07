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
    employee_code TEXT UNIQUE,
    address TEXT,
    place_of_birth TEXT,
    blood_type TEXT,
    date_of_birth TEXT,
    gender TEXT,
    civil_status TEXT,
    age INTEGER,
    contact_number TEXT,
    email TEXT,
    course TEXT,
    entity_office TEXT,
    bp_number TEXT,
    philhealth_number TEXT,
    pagibig_number TEXT,
    tin TEXT,
    id_number TEXT,
    position TEXT,
    salary_grade TEXT,
    basic_salary REAL,
    department TEXT,
    place_of_assignment TEXT,
    original_place_of_assignment TEXT,
    item_number TEXT,
    date_appointed TEXT,
    date_of_last_promotion TEXT,
    date_of_separation TEXT,
    employment_status TEXT,
    eligibility TEXT,
    photo_path TEXT,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# FACIAL DATA TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS facial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER UNIQUE,
    face_encoding BLOB,
    FOREIGN KEY(employee_id) REFERENCES employees(id)
)
""")

# ATTENDANCE TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    date TEXT,
    morning_in TEXT,
    lunch_out TEXT,
    afternoon_in TEXT,
    time_out TEXT,
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
