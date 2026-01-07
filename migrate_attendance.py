"""
Migration script to add new columns to attendance table for DTR support.
Run this once to update existing databases.
"""
import sqlite3

DB_NAME = "biometric.db"

def migrate_attendance():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        # Check if columns already exist
        cur.execute("PRAGMA table_info(attendance)")
        columns = [col[1] for col in cur.fetchall()]
        
        # Add new columns if they don't exist
        if 'lunch_out' not in columns:
            cur.execute("ALTER TABLE attendance ADD COLUMN lunch_out TEXT")
            print("✅ Added lunch_out column")
        
        if 'afternoon_in' not in columns:
            cur.execute("ALTER TABLE attendance ADD COLUMN afternoon_in TEXT")
            print("✅ Added afternoon_in column")
        
        if 'time_out' not in columns:
            cur.execute("ALTER TABLE attendance ADD COLUMN time_out TEXT")
            print("✅ Added time_out column")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_attendance()
