import sqlite3

conn = sqlite3.connect("biometric.db")
cur = conn.cursor()

cur.execute("DELETE FROM attendance")
cur.execute("DELETE FROM facial_data")
cur.execute("DELETE FROM employee")

# Reset auto-increment counters
cur.execute("DELETE FROM sqlite_sequence WHERE name='attendance'")
cur.execute("DELETE FROM sqlite_sequence WHERE name='facial_data'")
cur.execute("DELETE FROM sqlite_sequence WHERE name='employee'")

conn.commit()
conn.close()

print("✅ SYSTEM RESET COMPLETE: All employees erased")
