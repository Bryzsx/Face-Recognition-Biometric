"""
Unit tests for helper functions
"""
import unittest
from utils.helpers import (
    check_if_late,
    is_morning_time_in_allowed,
    is_afternoon_time_in_allowed,
    is_lunch_time_allowed
)


class TestHelpers(unittest.TestCase):
    """Test cases for helper functions"""
    
    def test_check_if_late_morning_early(self):
        """Test check_if_late for early morning time"""
        result = check_if_late("07:00 AM", "morning")
        self.assertFalse(result)
    
    def test_check_if_late_morning_on_time(self):
        """Test check_if_late for on-time morning"""
        result = check_if_late("08:00 AM", "morning")
        self.assertFalse(result)
    
    def test_check_if_late_morning_late(self):
        """Test check_if_late for late morning"""
        result = check_if_late("08:30 AM", "morning")
        self.assertTrue(result)
    
    def test_check_if_late_afternoon_on_time(self):
        """Test check_if_late for on-time afternoon"""
        result = check_if_late("12:30 PM", "afternoon")
        self.assertFalse(result)
    
    def test_check_if_late_afternoon_late(self):
        """Test check_if_late for late afternoon"""
        result = check_if_late("02:00 PM", "afternoon")
        self.assertTrue(result)
    
    def test_is_morning_time_in_allowed_early(self):
        """Test is_morning_time_in_allowed for early time"""
        result = is_morning_time_in_allowed("04:00 AM")
        self.assertFalse(result)
    
    def test_is_morning_time_in_allowed_valid(self):
        """Test is_morning_time_in_allowed for valid time"""
        result = is_morning_time_in_allowed("06:00 AM")
        self.assertTrue(result)
    
    def test_is_afternoon_time_in_allowed(self):
        """Test is_afternoon_time_in_allowed (always True)"""
        result = is_afternoon_time_in_allowed("01:00 PM")
        self.assertTrue(result)
    
    def test_is_lunch_time_allowed_valid(self):
        """Test is_lunch_time_allowed - should always return True (no restriction)"""
        result = is_lunch_time_allowed("12:00 PM")
        self.assertTrue(result)
    
    def test_is_lunch_time_allowed_early(self):
        """Test is_lunch_time_allowed for early time - should always return True"""
        result = is_lunch_time_allowed("11:00 AM")
        self.assertTrue(result)
    
    def test_is_lunch_time_allowed_late(self):
        """Test is_lunch_time_allowed for late time - should always return True"""
        result = is_lunch_time_allowed("02:00 PM")
        self.assertTrue(result)
    
    def test_is_lunch_time_allowed_any_time(self):
        """Test is_lunch_time_allowed for any time - should always return True (no restriction)"""
        # Test various times to ensure no restriction
        self.assertTrue(is_lunch_time_allowed("09:00 AM"))
        self.assertTrue(is_lunch_time_allowed("10:30 AM"))
        self.assertTrue(is_lunch_time_allowed("03:00 PM"))
        self.assertTrue(is_lunch_time_allowed("04:00 PM"))


if __name__ == '__main__':
    unittest.main()
