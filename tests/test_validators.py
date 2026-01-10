"""
Unit tests for input validators
"""
import unittest
from utils.validators import (
    ValidationError,
    validate_required,
    validate_email,
    validate_phone,
    validate_integer,
    validate_float,
    validate_date,
    validate_time,
    validate_employee_code,
    validate_name,
    validate_username,
    validate_password,
    sanitize_string,
    validate_employee_registration_data
)


class TestValidators(unittest.TestCase):
    """Test cases for validation functions"""
    
    def test_validate_required_valid(self):
        """Test validate_required with valid input"""
        result = validate_required("test", "Test Field")
        self.assertEqual(result, "test")
    
    def test_validate_required_empty(self):
        """Test validate_required with empty input"""
        with self.assertRaises(ValidationError):
            validate_required("", "Test Field")
    
    def test_validate_required_none(self):
        """Test validate_required with None input"""
        with self.assertRaises(ValidationError):
            validate_required(None, "Test Field")
    
    def test_validate_email_valid(self):
        """Test validate_email with valid email"""
        result = validate_email("test@example.com", "Email")
        self.assertEqual(result, "test@example.com")
    
    def test_validate_email_invalid(self):
        """Test validate_email with invalid email"""
        with self.assertRaises(ValidationError):
            validate_email("invalid-email", "Email")
    
    def test_validate_email_empty(self):
        """Test validate_email with empty email (optional)"""
        result = validate_email("", "Email")
        self.assertEqual(result, "")
    
    def test_validate_phone_valid(self):
        """Test validate_phone with valid phone number"""
        result = validate_phone("1234567890", "Phone")
        self.assertEqual(result, "1234567890")
    
    def test_validate_phone_with_dashes(self):
        """Test validate_phone with formatted phone number"""
        result = validate_phone("123-456-7890", "Phone")
        self.assertEqual(result, "123-456-7890")
    
    def test_validate_phone_empty(self):
        """Test validate_phone with empty phone (optional)"""
        result = validate_phone("", "Phone")
        self.assertEqual(result, "")
    
    def test_validate_integer_valid(self):
        """Test validate_integer with valid integer"""
        result = validate_integer("123", "Age")
        self.assertEqual(result, 123)
    
    def test_validate_integer_none(self):
        """Test validate_integer with None (optional)"""
        result = validate_integer(None, "Age")
        self.assertIsNone(result)
    
    def test_validate_integer_invalid(self):
        """Test validate_integer with invalid input"""
        with self.assertRaises(ValidationError):
            validate_integer("abc", "Age")
    
    def test_validate_integer_min_max(self):
        """Test validate_integer with min/max constraints"""
        result = validate_integer("25", "Age", min_value=18, max_value=100)
        self.assertEqual(result, 25)
        
        with self.assertRaises(ValidationError):
            validate_integer("15", "Age", min_value=18, max_value=100)
    
    def test_validate_float_valid(self):
        """Test validate_float with valid float"""
        result = validate_float("123.45", "Salary")
        self.assertEqual(result, 123.45)
    
    def test_validate_float_none(self):
        """Test validate_float with None (optional)"""
        result = validate_float(None, "Salary")
        self.assertIsNone(result)
    
    def test_validate_date_valid(self):
        """Test validate_date with valid date"""
        result = validate_date("2025-01-15", "Date")
        self.assertEqual(result, "2025-01-15")
    
    def test_validate_date_invalid(self):
        """Test validate_date with invalid date format"""
        with self.assertRaises(ValidationError):
            validate_date("15/01/2025", "Date")
    
    def test_validate_time_valid(self):
        """Test validate_time with valid time"""
        result = validate_time("08:00 AM", "Time")
        self.assertEqual(result, "08:00 AM")
    
    def test_validate_time_invalid(self):
        """Test validate_time with invalid time format"""
        with self.assertRaises(ValidationError):
            validate_time("25:00", "Time")
    
    def test_validate_employee_code_valid(self):
        """Test validate_employee_code with valid code"""
        result = validate_employee_code("EMP001")
        self.assertEqual(result, "EMP001")
    
    def test_validate_employee_code_invalid(self):
        """Test validate_employee_code with invalid characters"""
        with self.assertRaises(ValidationError):
            validate_employee_code("EMP@001")
    
    def test_validate_name_valid(self):
        """Test validate_name with valid name"""
        result = validate_name("John Doe", "Name")
        self.assertEqual(result, "John Doe")
    
    def test_validate_name_invalid(self):
        """Test validate_name with invalid characters"""
        with self.assertRaises(ValidationError):
            validate_name("John123", "Name")
    
    def test_validate_username_valid(self):
        """Test validate_username with valid username"""
        result = validate_username("john_doe")
        self.assertEqual(result, "john_doe")
    
    def test_validate_username_invalid(self):
        """Test validate_username with invalid characters"""
        with self.assertRaises(ValidationError):
            validate_username("John Doe")
    
    def test_validate_password_valid(self):
        """Test validate_password with valid password"""
        result = validate_password("password123", min_length=6)
        self.assertEqual(result, "password123")
    
    def test_validate_password_too_short(self):
        """Test validate_password with too short password"""
        with self.assertRaises(ValidationError):
            validate_password("pass", min_length=6)
    
    def test_sanitize_string(self):
        """Test sanitize_string function"""
        result = sanitize_string("  test  ", max_length=10)
        self.assertEqual(result, "test")
    
    def test_sanitize_string_max_length(self):
        """Test sanitize_string with max length"""
        result = sanitize_string("this is a very long string", max_length=10)
        self.assertEqual(result, "this is a ")
    
    def test_validate_employee_registration_data_valid(self):
        """Test validate_employee_registration_data with valid data"""
        data = {
            "full_name": "John Doe",
            "employee_id": "EMP001",
            "email": "john@example.com",
            "contact_number": "1234567890"
        }
        validated, errors = validate_employee_registration_data(data)
        self.assertEqual(len(errors), 0)
        self.assertEqual(validated["full_name"], "John Doe")
        self.assertEqual(validated["employee_code"], "EMP001")
    
    def test_validate_employee_registration_data_missing_required(self):
        """Test validate_employee_registration_data with missing required fields"""
        data = {
            "email": "john@example.com"
        }
        validated, errors = validate_employee_registration_data(data)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
