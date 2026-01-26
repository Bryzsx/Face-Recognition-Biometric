"""
Database connection utilities
"""
import sqlite3
import time
from flask import g
from config import DATABASE
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum retries for database operations
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # 100ms delay between retries


def get_db():
    """
    Get database connection from Flask's g object (request context)
    Enables WAL mode for better concurrent access and performance
    """
    if "db" not in g:
        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Reduced timeout to 10 seconds to fail faster and prevent long waits
                # WAL mode allows concurrent reads, so shorter timeout is acceptable
                g.db = sqlite3.connect(DATABASE, timeout=10.0)
                g.db.row_factory = sqlite3.Row
                
                # Enable WAL mode for concurrent reads (allows multiple readers simultaneously)
                # This is critical for handling concurrent requests
                g.db.execute("PRAGMA journal_mode=WAL")
                
                # Optimize for better performance and concurrency
                g.db.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still safe
                g.db.execute("PRAGMA cache_size=-64000")  # 64MB cache
                g.db.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
                g.db.execute("PRAGMA busy_timeout=10000")  # 10 second busy timeout (reduced from 30)
                g.db.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
                
                logger.debug("Database connection established")
                break  # Success, exit retry loop
            except sqlite3.OperationalError as e:
                retries += 1
                if "database is locked" in str(e).lower() or "database is busy" in str(e).lower():
                    if retries < MAX_RETRIES:
                        logger.warning(f"Database locked, retrying ({retries}/{MAX_RETRIES})...")
                        time.sleep(RETRY_DELAY * retries)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Database locked after {MAX_RETRIES} retries: {str(e)}")
                else:
                    logger.error(f"Database operational error: {str(e)}", exc_info=True)
                    # If connection exists but failed, clean it up
                    if "db" in g:
                        try:
                            g.db.close()
                        except Exception:
                            pass
                        del g.db
                    raise
            except Exception as e:
                logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
                # Clean up on any error
                if "db" in g:
                    try:
                        g.db.close()
                    except Exception:
                        pass
                    del g.db
                raise
        
        # If we exhausted retries, raise an error
        if "db" not in g:
            raise sqlite3.OperationalError("Database connection failed after retries")
    
    return g.db


def close_db(exception=None):
    """Close database connection at the end of request"""
    db = g.pop("db", None)
    if db is not None:
        try:
            # Rollback any uncommitted transactions before closing
            try:
                db.rollback()
            except Exception:
                pass
            
            db.close()
            logger.debug("Database connection closed")
        except sqlite3.ProgrammingError:
            # Connection already closed, ignore
            pass
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}", exc_info=True)
        finally:
            # Ensure connection is removed from g even if close failed
            if "db" in g:
                try:
                    g.db.close()
                except Exception:
                    pass
                g.pop("db", None)
    
    if exception:
        logger.error(f"Exception in teardown: {str(exception)}", exc_info=True)
