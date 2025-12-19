import sqlite3

def get_db():
    conn = sqlite3.connect("biometric.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
