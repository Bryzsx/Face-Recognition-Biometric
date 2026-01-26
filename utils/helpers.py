"""
Helper functions for attendance and time calculations
"""
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

# Cache for time settings to avoid repeated database queries
_time_settings_cache = None
_cache_timestamp = None


def get_time_settings():
    """
    Get time settings from database with caching.
    Returns a dictionary of time settings.
    """
    global _time_settings_cache, _cache_timestamp
    
    # Cache for 5 minutes
    if _time_settings_cache and _cache_timestamp:
        from time import time
        if time() - _cache_timestamp < 300:  # 5 minutes
            return _time_settings_cache
    
    try:
        from config import DATABASE
        import sqlite3
        
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        cur.execute("""
            SELECT setting_key, setting_value 
            FROM settings 
            WHERE setting_key IN ('morning_in_start', 'morning_in_late', 'morning_in_window_end',
                                  'lunch_out_start', 'lunch_out_end',
                                  'afternoon_in_start', 'afternoon_in_late', 'afternoon_in_window_end', 
                                  'time_out_start')
        """)
        
        settings = {}
        for row in cur.fetchall():
            key = row["setting_key"]
            value = row["setting_value"]
            settings[key] = value
        
        db.close()
        
        # Set defaults if not found
        defaults = {
            "morning_in_start": "06:00 AM",
            "morning_in_late": "08:00 AM",
            "morning_in_window_end": "10:00 AM",
            "lunch_out_start": "10:00 AM",
            "lunch_out_end": "12:15 PM",
            "afternoon_in_start": "12:16 PM",
            "afternoon_in_late": "01:00 PM",
            "afternoon_in_window_end": "02:00 PM",
            "time_out_start": "05:00 PM"
        }
        
        for key, default_value in defaults.items():
            if key not in settings:
                settings[key] = default_value
        
        _time_settings_cache = settings
        from time import time
        _cache_timestamp = time()
        
        return settings
    except Exception as e:
        logger.error(f"Error loading time settings: {str(e)}", exc_info=True)
        # Return defaults on error
        return {
            "morning_in_start": "06:00 AM",
            "morning_in_late": "08:00 AM",
            "morning_in_window_end": "10:00 AM",
            "lunch_out_start": "10:00 AM",
            "lunch_out_end": "12:15 PM",
            "afternoon_in_start": "12:16 PM",
            "afternoon_in_late": "01:00 PM",
            "afternoon_in_window_end": "02:00 PM",
            "time_out_start": "05:00 PM"
        }


def clear_time_settings_cache():
    """Clear the time settings cache to force reload from database"""
    global _time_settings_cache, _cache_timestamp
    _time_settings_cache = None
    _cache_timestamp = None


def check_if_late(time_str, time_type="morning"):
    """
    Check if a time string is late based on the configured late thresholds.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM" (e.g., "08:01 AM")
        time_type: "morning" or "afternoon"
    
    Returns:
        bool: True if late, False if on-time
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        settings = get_time_settings()
        
        if time_type == "morning":
            late_threshold_str = settings.get("morning_in_late", "08:00 AM")
            # Add 1 minute to the late threshold
            late_threshold = datetime.strptime(late_threshold_str, "%I:%M %p")
            from datetime import timedelta
            late_threshold = late_threshold + timedelta(minutes=1)
            return time_obj >= late_threshold
        elif time_type == "afternoon":
            late_threshold_str = settings.get("afternoon_in_late", "01:00 PM")
            # Add 1 minute to the late threshold
            late_threshold = datetime.strptime(late_threshold_str, "%I:%M %p")
            from datetime import timedelta
            late_threshold = late_threshold + timedelta(minutes=1)
            return time_obj >= late_threshold
        
        return False
    except Exception as e:
        logger.error(f"Error checking late status: {str(e)}", exc_info=True)
        return False


def is_morning_time_in_allowed(time_str):
    """
    Check if morning time-in is allowed within the configured window.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True if allowed (within window), False otherwise
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        settings = get_time_settings()
        start_time_str = settings.get("morning_in_start", "06:00 AM")
        window_end_str = settings.get("morning_in_window_end", "10:00 AM")
        
        start_time = datetime.strptime(start_time_str, "%I:%M %p")
        window_end = datetime.strptime(window_end_str, "%I:%M %p")
        
        return start_time <= time_obj <= window_end
    except Exception as e:
        logger.error(f"Error checking morning time-in: {str(e)}", exc_info=True)
        return False


def is_afternoon_time_in_allowed(time_str):
    """
    Check if afternoon time-in is allowed within the configured window.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True if allowed (within window), False otherwise
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        settings = get_time_settings()
        start_time_str = settings.get("afternoon_in_start", "12:16 PM")
        window_end_str = settings.get("afternoon_in_window_end", "02:00 PM")
        
        start_time = datetime.strptime(start_time_str, "%I:%M %p")
        window_end = datetime.strptime(window_end_str, "%I:%M %p")
        
        return start_time <= time_obj <= window_end
    except Exception as e:
        logger.error(f"Error checking afternoon time-in: {str(e)}", exc_info=True)
        return False


def is_lunch_time_allowed(time_str):
    """
    Check if lunch out time is allowed within the configured window.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True if allowed (within window), False otherwise
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        settings = get_time_settings()
        start_time_str = settings.get("lunch_out_start", "10:00 AM")
        end_time_str = settings.get("lunch_out_end", "12:15 PM")
        
        start_time = datetime.strptime(start_time_str, "%I:%M %p")
        end_time = datetime.strptime(end_time_str, "%I:%M %p")
        
        return start_time <= time_obj <= end_time
    except Exception as e:
        logger.error(f"Error checking lunch time: {str(e)}", exc_info=True)
        return False


def is_time_out_allowed(time_str):
    """
    Check if end of day time-out is allowed (from configured start time onwards).
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True if allowed (from start time onwards), False otherwise
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        settings = get_time_settings()
        start_time_str = settings.get("time_out_start", "05:00 PM")
        start_time = datetime.strptime(start_time_str, "%I:%M %p")
        
        return time_obj >= start_time
    except Exception as e:
        logger.error(f"Error checking time-out: {str(e)}", exc_info=True)
        return False
