"""
Quick script to check if employees exist in the database
"""
import sqlite3

DB_NAME = "biometric.db"

try:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Check if employees table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
    table_exists = cur.fetchone()
    
    if not table_exists:
        print("❌ ERROR: 'employees' table does not exist!")
        print("   Please run: python init_db.py")
    else:
        # Count employees
        cur.execute("SELECT COUNT(*) FROM employees")
        count = cur.fetchone()[0]
        print(f"✅ Found {count} employee(s) in the database")
        
        if count > 0:
            # List all employees
            cur.execute("SELECT id, full_name, employee_code, department FROM employees ORDER BY id")
            employees = cur.fetchall()
            print("\nEmployee List:")
            print("-" * 60)
            for emp in employees:
                print(f"ID: {emp[0]}, Name: {emp[1] or 'N/A'}, Code: {emp[2] or 'N/A'}, Dept: {emp[3] or 'N/A'}")
        else:
            print("\n⚠️  No employees found in database.")
            print("   Please register an employee through the web interface.")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
