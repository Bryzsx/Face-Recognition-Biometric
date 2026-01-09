#!/usr/bin/env python3
"""
Script to add database indexes for better performance.
Run this once to optimize database queries.
"""

import sqlite3
import os

DB_NAME = "biometric.db"

def add_indexes():
    """Add indexes to improve query performance"""
    if not os.path.exists(DB_NAME):
        print(f"❌ Database {DB_NAME} not found!")
        return False
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        print("🔧 Adding database indexes for better performance...")
        
        # Index on attendance.date - used frequently in WHERE clauses
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date 
            ON attendance(date)
        """)
        print("✅ Created index: idx_attendance_date")
        
        # Index on attendance.attendance_status - used in WHERE clauses
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_status 
            ON attendance(attendance_status)
        """)
        print("✅ Created index: idx_attendance_status")
        
        # Composite index on date and status - for common queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date_status 
            ON attendance(date, attendance_status)
        """)
        print("✅ Created index: idx_attendance_date_status")
        
        # Index on attendance.employee_id - used in JOINs
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_employee_id 
            ON attendance(employee_id)
        """)
        print("✅ Created index: idx_attendance_employee_id")
        
        # Index on employees.employee_code - used in searches
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_employees_code 
            ON employees(employee_code)
        """)
        print("✅ Created index: idx_employees_code")
        
        # Index on employees.full_name - used in searches and ordering
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_employees_name 
            ON employees(full_name)
        """)
        print("✅ Created index: idx_employees_name")
        
        conn.commit()
        print("\n✅ All indexes created successfully!")
        print("📊 Database performance should be significantly improved.")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating indexes: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    add_indexes()
