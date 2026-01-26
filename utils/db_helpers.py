"""
Database helper utilities for safe query execution with retry logic
"""
import sqlite3
import time
from functools import wraps
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_QUERY_RETRIES = 3
QUERY_RETRY_DELAY = 0.1  # 100ms


def db_query_with_retry(func):
    """
    Decorator to retry database queries on lock/busy errors
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        last_exception = None
        
        while retries < MAX_QUERY_RETRIES:
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if "database is locked" in error_msg or "database is busy" in error_msg:
                    retries += 1
                    if retries < MAX_QUERY_RETRIES:
                        wait_time = QUERY_RETRY_DELAY * retries
                        logger.debug(f"Database busy, retrying query in {wait_time}s ({retries}/{MAX_QUERY_RETRIES})...")
                        time.sleep(wait_time)
                        last_exception = e
                        continue
                    else:
                        logger.error(f"Query failed after {MAX_QUERY_RETRIES} retries: {str(e)}")
                        raise
                else:
                    # Not a lock error, don't retry
                    raise
            except Exception as e:
                # Other errors, don't retry
                raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise sqlite3.OperationalError("Query failed after retries")
    
    return wrapper


def execute_query_safe(db, query, params=None, fetch_one=False, fetch_all=False):
    """
    Safely execute a database query with retry logic
    
    Args:
        db: Database connection
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: If True, return single row
        fetch_all: If True, return all rows
    
    Returns:
        Query result based on fetch_one/fetch_all flags
    """
    retries = 0
    last_exception = None
    
    while retries < MAX_QUERY_RETRIES:
        try:
            cur = db.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            if fetch_one:
                return cur.fetchone()
            elif fetch_all:
                return cur.fetchall()
            else:
                return cur
            
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if "database is locked" in error_msg or "database is busy" in error_msg:
                retries += 1
                if retries < MAX_QUERY_RETRIES:
                    wait_time = QUERY_RETRY_DELAY * retries
                    logger.debug(f"Database busy during query, retrying in {wait_time}s ({retries}/{MAX_QUERY_RETRIES})...")
                    time.sleep(wait_time)
                    last_exception = e
                    continue
                else:
                    logger.error(f"Query failed after {MAX_QUERY_RETRIES} retries: {str(e)}")
                    raise
            else:
                raise
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}", exc_info=True)
            raise
    
    if last_exception:
        raise last_exception
    raise sqlite3.OperationalError("Query execution failed after retries")
