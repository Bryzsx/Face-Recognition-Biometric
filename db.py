"""
Database connection utilities
"""
import sqlite3
from flask import g
from config import DATABASE
from utils.logger import get_logger

logger = get_logger(__name__)


def get_db():
    """
    Get database connection from Flask's g object (request context)
    Enables WAL mode for better concurrent access and performance
    """
    if "db" not in g:
        try:
            g.db = sqlite3.connect(DATABASE, timeout=20.0)
            g.db.row_factory = sqlite3.Row
            
            # Enable WAL mode for concurrent reads (allows multiple readers simultaneously)
            g.db.execute("PRAGMA journal_mode=WAL")
            
            # Optimize for better performance
            g.db.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still safe
            g.db.execute("PRAGMA cache_size=-64000")  # 64MB cache
            g.db.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            
            logger.debug("Database connection established")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
            raise
    
    return g.db


def close_db(exception=None):
    """Close database connection at the end of request"""
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
            logger.debug("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}", exc_info=True)
    
    if exception:
        logger.error(f"Exception in teardown: {str(exception)}", exc_info=True)
