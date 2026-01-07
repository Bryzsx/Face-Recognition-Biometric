"""
Migration script to add photo_path column to employees table
"""
import sqlite3

DB_NAME = "biometric.db"

def migrate_photo_column():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        # Check if column already exists
        cur.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'photo_path' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN photo_path TEXT")
            conn.commit()
            print("✅ Added photo_path column to employees table")
        else:
            print("✅ photo_path column already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("Migrating employees table to add photo_path column...")
    print("=" * 50)
    success = migrate_photo_column()
    print("=" * 50)
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
