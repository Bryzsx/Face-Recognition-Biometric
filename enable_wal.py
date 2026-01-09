#!/usr/bin/env python3
"""
Script to enable WAL mode on the database for better concurrent access.
This allows multiple processes to read from the database simultaneously.
"""

import sqlite3
import os

DB_NAME = "biometric.db"

def enable_wal():
    """Enable WAL mode and optimize database settings"""
    if not os.path.exists(DB_NAME):
        print(f"❌ Database {DB_NAME} not found!")
        return False
    
    conn = sqlite3.connect(DB_NAME, timeout=20.0)
    cur = conn.cursor()
    
    try:
        print("🔧 Enabling WAL mode and optimizing database...")
        
        # Enable WAL mode (Write-Ahead Logging)
        # This allows multiple readers and one writer simultaneously
        cur.execute("PRAGMA journal_mode=WAL")
        result = cur.fetchone()
        print(f"✅ Journal mode: {result[0]}")
        
        # Optimize synchronous mode (NORMAL is faster than FULL, still safe)
        cur.execute("PRAGMA synchronous=NORMAL")
        print("✅ Synchronous mode: NORMAL")
        
        # Increase cache size for better performance (64MB)
        cur.execute("PRAGMA cache_size=-64000")
        print("✅ Cache size: 64MB")
        
        # Store temporary tables in memory for faster operations
        cur.execute("PRAGMA temp_store=MEMORY")
        print("✅ Temp store: MEMORY")
        
        # Optimize for better query performance
        cur.execute("PRAGMA optimize")
        print("✅ Database optimized")
        
        conn.commit()
        print("\n✅ Database optimization complete!")
        print("📊 The database now supports concurrent access much better.")
        print("   Multiple users can access the system simultaneously without locking issues.")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error optimizing database: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    enable_wal()
