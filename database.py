import sqlite3

DB_NAME = "biometric.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        employee_id TEXT UNIQUE NOT NULL,
        department TEXT,
        position TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()
    db.close()
