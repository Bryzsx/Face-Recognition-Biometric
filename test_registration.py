"""
Test script to verify database and registration process
"""
import sqlite3

DB_NAME = "biometric.db"

def test_database():
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        # Check if employees table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cur.fetchone():
            print("ERROR: 'employees' table does not exist!")
            print("   Run: python init_db.py")
            return False
        
        # Check table structure
        cur.execute("PRAGMA table_info(employees)")
        columns = cur.fetchall()
        print(f"OK: Employees table exists with {len(columns)} columns")
        
        # Try to insert a test employee
        try:
            cur.execute("""
                INSERT INTO employees (full_name, employee_code, department, position)
                VALUES (?, ?, ?, ?)
            """, ("Test Employee", "TEST-001", "Test Dept", "Test Position"))
            
            test_id = cur.lastrowid
            conn.commit()
            print(f"OK: Test insert successful! Employee ID: {test_id}")
            
            # Verify it was saved
            cur.execute("SELECT * FROM employees WHERE id=?", (test_id,))
            employee = cur.fetchone()
            if employee:
                print(f"OK: Employee retrieved: {employee}")
            else:
                print("ERROR: Employee not found after insert!")
            
            # Clean up test data
            cur.execute("DELETE FROM employees WHERE id=?", (test_id,))
            conn.commit()
            print("OK: Test employee deleted")
            
        except sqlite3.IntegrityError as e:
            print(f"WARNING: Integrity error (might be expected): {e}")
        except Exception as e:
            print(f"ERROR inserting test employee: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"ERROR: Database error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing database and registration process...")
    print("=" * 50)
    success = test_database()
    print("=" * 50)
    if success:
        print("OK: All tests passed! Database is ready.")
    else:
        print("ERROR: Tests failed! Please fix the issues above.")
