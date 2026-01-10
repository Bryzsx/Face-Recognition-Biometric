"""
Helper functions for attendance and time calculations
"""
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


def check_if_late(time_str, time_type="morning"):
    """
    Check if a time string is late based on the time windows.
    
    Morning: 5:00 AM - 8:00 AM (on-time), 8:01 AM onwards (late)
    Afternoon: 12:00 PM - 1:00 PM (on-time), 1:01 PM onwards (late)
    
    Args:
        time_str: Time string in format "HH:MM AM/PM" (e.g., "08:01 AM")
        time_type: "morning" or "afternoon"
    
    Returns:
        bool: True if late, False if on-time
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        
        if time_type == "morning":
            late_threshold = datetime.strptime("08:01 AM", "%I:%M %p")
            return time_obj >= late_threshold
        elif time_type == "afternoon":
            late_threshold = datetime.strptime("01:01 PM", "%I:%M %p")
            return time_obj >= late_threshold
        
        return False
    except Exception as e:
        logger.error(f"Error checking late status: {str(e)}", exc_info=True)
        return False


def is_morning_time_in_allowed(time_str):
    """
    Check if morning time-in is allowed.
    Employees can time in from 5:00 AM onwards.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True if allowed, False otherwise
    """
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        min_time = datetime.strptime("05:00 AM", "%I:%M %p")
        return time_obj >= min_time
    except Exception as e:
        logger.error(f"Error checking morning time-in: {str(e)}", exc_info=True)
        return False


def is_afternoon_time_in_allowed(time_str):
    """
    Check if afternoon time-in is allowed.
    Employees can time in at any time (no restriction).
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True (always allowed, no time restriction)
    """
    return True


def is_lunch_time_allowed(time_str):
    """
    Check if lunch out time is allowed.
    Employees can time out for lunch at any time (no restriction).
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
    
    Returns:
        bool: True (always allowed, no time restriction)
    """
    return True
