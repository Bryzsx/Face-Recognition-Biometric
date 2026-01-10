"""
Input validation utilities for the Face Recognition Biometric System
"""
import re
from datetime import datetime
from typing import Optional, Tuple, Dict, Any


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_required(value: Any, field_name: str) -> str:
    """
    Validate that a required field is not empty
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
    
    Returns:
        Stripped string value
    
    Raises:
        ValidationError: If value is empty or None
    """
    if value is None:
        raise ValidationError(f"{field_name} is required")
    
    value_str = str(value).strip()
    if not value_str:
        raise ValidationError(f"{field_name} is required")
    
    return value_str


def validate_length(value: str, field_name: str, min_length: int = None, max_length: int = None) -> str:
    """
    Validate string length
    
    Args:
        value: The string to validate
        field_name: Name of the field for error messages
        min_length: Minimum length (optional)
        max_length: Maximum length (optional)
    
    Returns:
        Validated string
    
    Raises:
        ValidationError: If length constraints are not met
    """
    value_str = str(value).strip()
    length = len(value_str)
    
    if min_length is not None and length < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long")
    
    if max_length is not None and length > max_length:
        raise ValidationError(f"{field_name} must be no more than {max_length} characters long")
    
    return value_str


def validate_email(email: str, field_name: str = "Email") -> str:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated email address (lowercase)
    
    Raises:
        ValidationError: If email format is invalid
    """
    if not email or not email.strip():
        return ""  # Email is optional, return empty string
    
    email = email.strip().lower()
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError(f"{field_name} has an invalid format")
    
    if len(email) > 255:
        raise ValidationError(f"{field_name} is too long (maximum 255 characters)")
    
    return email


def validate_phone(phone: str, field_name: str = "Phone number") -> str:
    """
    Validate phone number format (flexible - allows various formats)
    
    Args:
        phone: Phone number to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated phone number
    
    Raises:
        ValidationError: If phone format is invalid
    """
    if not phone or not phone.strip():
        return ""  # Phone is optional
    
    phone = phone.strip()
    
    # Remove common separators for validation
    digits_only = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Allow digits, optional + at start, and reasonable length (7-15 digits)
    if not re.match(r'^\+?[0-9]{7,15}$', digits_only):
        raise ValidationError(f"{field_name} has an invalid format")
    
    return phone


def validate_integer(value: Any, field_name: str, min_value: int = None, max_value: int = None) -> Optional[int]:
    """
    Validate and convert to integer
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
    
    Returns:
        Integer value or None if empty
    
    Raises:
        ValidationError: If value cannot be converted or is out of range
    """
    if value is None or value == "":
        return None
    
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(f"{field_name} must be no more than {max_value}")
    
    return int_value


def validate_float(value: Any, field_name: str, min_value: float = None, max_value: float = None) -> Optional[float]:
    """
    Validate and convert to float
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
    
    Returns:
        Float value or None if empty
    
    Raises:
        ValidationError: If value cannot be converted or is out of range
    """
    if value is None or value == "":
        return None
    
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number")
    
    if min_value is not None and float_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")
    
    if max_value is not None and float_value > max_value:
        raise ValidationError(f"{field_name} must be no more than {max_value}")
    
    return float_value


def validate_date(date_str: str, field_name: str = "Date", date_format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Validate date format
    
    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages
        date_format: Expected date format (default: YYYY-MM-DD)
    
    Returns:
        Validated date string or None if empty
    
    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip()
    
    try:
        datetime.strptime(date_str, date_format)
        return date_str
    except ValueError:
        raise ValidationError(f"{field_name} must be in format {date_format}")


def validate_time(time_str: str, field_name: str = "Time", time_format: str = "%I:%M %p") -> Optional[str]:
    """
    Validate time format (HH:MM AM/PM)
    
    Args:
        time_str: Time string to validate
        field_name: Name of the field for error messages
        time_format: Expected time format (default: %I:%M %p)
    
    Returns:
        Validated time string or None if empty
    
    Raises:
        ValidationError: If time format is invalid
    """
    if not time_str or not time_str.strip():
        return None
    
    time_str = time_str.strip()
    
    try:
        datetime.strptime(time_str, time_format)
        return time_str
    except ValueError:
        raise ValidationError(f"{field_name} must be in format {time_format} (e.g., '08:00 AM')")


def validate_employee_code(code: str) -> str:
    """
    Validate employee code format
    
    Args:
        code: Employee code to validate
    
    Returns:
        Validated employee code
    
    Raises:
        ValidationError: If employee code format is invalid
    """
    code = validate_required(code, "Employee Code")
    code = validate_length(code, "Employee Code", min_length=3, max_length=50)
    
    # Allow alphanumeric, dashes, underscores
    if not re.match(r'^[A-Za-z0-9\-_]+$', code):
        raise ValidationError("Employee Code can only contain letters, numbers, dashes, and underscores")
    
    return code.upper()


def validate_name(name: str, field_name: str = "Name") -> str:
    """
    Validate person name (allows letters, spaces, apostrophes, hyphens)
    
    Args:
        name: Name to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated name
    
    Raises:
        ValidationError: If name format is invalid
    """
    name = validate_required(name, field_name)
    name = validate_length(name, field_name, min_length=2, max_length=255)
    
    # Allow letters, spaces, apostrophes, hyphens, periods, commas
    if not re.match(r'^[A-Za-z\s\'\-\,\.]+$', name):
        raise ValidationError(f"{field_name} can only contain letters, spaces, apostrophes, hyphens, periods, and commas")
    
    return name.strip()


def validate_username(username: str) -> str:
    """
    Validate username format
    
    Args:
        username: Username to validate
    
    Returns:
        Validated username
    
    Raises:
        ValidationError: If username format is invalid
    """
    username = validate_required(username, "Username")
    username = username.strip().lower()
    username = validate_length(username, "Username", min_length=3, max_length=50)
    
    # Allow alphanumeric and underscores only
    if not re.match(r'^[a-z0-9_]+$', username):
        raise ValidationError("Username can only contain lowercase letters, numbers, and underscores")
    
    return username


def validate_password(password: str, min_length: int = 6) -> str:
    """
    Validate password (basic validation)
    
    Args:
        password: Password to validate
        min_length: Minimum password length
    
    Returns:
        Validated password
    
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    password = validate_required(password, "Password")
    password = validate_length(password, "Password", min_length=min_length, max_length=128)
    
    return password


def validate_base64_image(image_data: str, field_name: str = "Image") -> str:
    """
    Validate base64 image data
    
    Args:
        image_data: Base64 image string
        field_name: Name of the field for error messages
    
    Returns:
        Validated base64 string
    
    Raises:
        ValidationError: If image data is invalid
    """
    if not image_data or not image_data.strip():
        raise ValidationError(f"{field_name} is required")
    
    # Remove data URL prefix if present
    if ',' in image_data:
        image_data = image_data.split(',', 1)[1]
    
    # Check if it's valid base64
    try:
        import base64
        base64.b64decode(image_data, validate=True)
    except Exception:
        raise ValidationError(f"{field_name} is not a valid base64 image")
    
    return image_data


def sanitize_string(value: str, max_length: int = None) -> str:
    """
    Sanitize string input (strip whitespace, limit length)
    
    Args:
        value: String to sanitize
        max_length: Maximum length (optional)
    
    Returns:
        Sanitized string
    """
    if value is None:
        return ""
    
    sanitized = str(value).strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_employee_registration_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], list]:
    """
    Validate all employee registration form data
    
    Args:
        data: Dictionary containing form data
    
    Returns:
        Tuple of (validated_data, errors_list)
    """
    validated = {}
    errors = []
    
    try:
        # Required fields
        validated['full_name'] = validate_name(data.get('full_name', ''), "Full Name")
        validated['employee_code'] = validate_employee_code(data.get('employee_id', ''))
        
        # Optional fields
        validated['address'] = sanitize_string(data.get('address', ''), max_length=500)
        validated['place_of_birth'] = sanitize_string(data.get('place_of_birth', ''), max_length=100)
        validated['blood_type'] = sanitize_string(data.get('blood_type', ''), max_length=10)
        validated['date_of_birth'] = validate_date(data.get('date_of_birth', ''), "Date of Birth")
        validated['gender'] = sanitize_string(data.get('gender', ''), max_length=20)
        validated['civil_status'] = sanitize_string(data.get('civil_status', ''), max_length=20)
        validated['age'] = validate_integer(data.get('age', ''), "Age", min_value=16, max_value=100)
        validated['contact_number'] = validate_phone(data.get('contact_number', ''), "Contact Number")
        validated['email'] = validate_email(data.get('email', ''), "Email")
        validated['course'] = sanitize_string(data.get('course', ''), max_length=100)
        validated['entity_office'] = sanitize_string(data.get('entity_office', ''), max_length=200)
        validated['bp_number'] = sanitize_string(data.get('bp_number', ''), max_length=50)
        validated['philhealth_number'] = sanitize_string(data.get('philhealth_number', ''), max_length=50)
        validated['pagibig_number'] = sanitize_string(data.get('pagibig_number', ''), max_length=50)
        validated['tin'] = sanitize_string(data.get('tin', ''), max_length=50)
        validated['id_number'] = sanitize_string(data.get('id_number', ''), max_length=50)
        validated['position'] = sanitize_string(data.get('position', ''), max_length=100)
        validated['salary_grade'] = sanitize_string(data.get('salary_grade', ''), max_length=20)
        validated['basic_salary'] = validate_float(data.get('basic_salary', ''), "Basic Salary", min_value=0)
        validated['department'] = sanitize_string(data.get('department', ''), max_length=100)
        validated['place_of_assignment'] = sanitize_string(data.get('place_of_assignment', ''), max_length=200)
        validated['original_place_of_assignment'] = sanitize_string(data.get('original_place_of_assignment', ''), max_length=200)
        validated['item_number'] = sanitize_string(data.get('item_number', ''), max_length=50)
        validated['date_appointed'] = validate_date(data.get('date_appointed', ''), "Date Appointed")
        validated['date_of_last_promotion'] = validate_date(data.get('date_of_last_promotion', ''), "Date of Last Promotion")
        validated['date_of_separation'] = validate_date(data.get('date_of_separation', ''), "Date of Separation")
        validated['employment_status'] = sanitize_string(data.get('employment_status', ''), max_length=50)
        validated['eligibility'] = sanitize_string(data.get('eligibility', ''), max_length=100)
        
        # Face images (optional but validated if provided)
        face_images = data.get('face_images', '[]')
        if face_images and face_images != '[]':
            try:
                import json
                images = json.loads(face_images)
                validated['face_images'] = images
            except json.JSONDecodeError:
                errors.append("Invalid face images data format")
        
    except ValidationError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return validated, errors
