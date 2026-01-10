"""
Blueprints for Face Recognition Biometric System
"""
from .auth import auth_bp
from .admin import admin_bp
from .employee import employee_bp
from .api import api_bp

__all__ = ['auth_bp', 'admin_bp', 'employee_bp', 'api_bp']
