"""
Migration script to update employees table with all new fields
"""
import sqlite3

DB_NAME = "biometric.db"

def migrate_employees():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        # Get existing columns
        cur.execute("PRAGMA table_info(employees)")
        existing_columns = [col[1] for col in cur.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # List of all columns that should exist
        new_columns = {
            'address': 'TEXT',
            'place_of_birth': 'TEXT',
            'blood_type': 'TEXT',
            'date_of_birth': 'TEXT',
            'gender': 'TEXT',
            'civil_status': 'TEXT',
            'age': 'INTEGER',
            'contact_number': 'TEXT',
            'email': 'TEXT',
            'course': 'TEXT',
            'entity_office': 'TEXT',
            'bp_number': 'TEXT',
            'philhealth_number': 'TEXT',
            'pagibig_number': 'TEXT',
            'tin': 'TEXT',
            'id_number': 'TEXT',
            'salary_grade': 'TEXT',
            'basic_salary': 'REAL',
            'place_of_assignment': 'TEXT',
            'original_place_of_assignment': 'TEXT',
            'item_number': 'TEXT',
            'date_appointed': 'TEXT',
            'date_of_last_promotion': 'TEXT',
            'date_of_separation': 'TEXT',
            'employment_status': 'TEXT',
            'eligibility': 'TEXT',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        # Add missing columns
        added_count = 0
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cur.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_type}")
                    print(f"Added column: {col_name}")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    print(f"Warning: Could not add {col_name}: {e}")
        
        # Make employee_code UNIQUE if not already
        if 'employee_code' in existing_columns:
            try:
                # SQLite doesn't support ADD UNIQUE directly, so we'll skip this
                # The constraint should be in the CREATE TABLE statement
                pass
            except:
                pass
        
        conn.commit()
        
        if added_count > 0:
            print(f"\nOK: Migration complete! Added {added_count} new columns.")
        else:
            print("\nOK: All columns already exist. No migration needed.")
        
        # Verify final structure
        cur.execute("PRAGMA table_info(employees)")
        final_columns = cur.fetchall()
        print(f"\nFinal table has {len(final_columns)} columns:")
        for col in final_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("Migrating employees table...")
    print("=" * 50)
    success = migrate_employees()
    print("=" * 50)
    if success:
        print("OK: Migration successful!")
    else:
        print("ERROR: Migration failed!")
