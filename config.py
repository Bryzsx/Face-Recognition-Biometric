"""
Configuration settings for Face Recognition Biometric System
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Database configuration
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'biometric.db'))

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-a-random-secret-key-in-production')
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
PORT = int(os.environ.get('FLASK_PORT', 5000))

# SSL/HTTPS configuration
SSL_CERT_PATH = os.path.join(BASE_DIR, 'certs', 'server.crt')
SSL_KEY_PATH = os.path.join(BASE_DIR, 'certs', 'server.key')

# Logging configuration
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Face recognition configuration
FACE_RECOGNITION_TOLERANCE = float(os.environ.get('FACE_RECOGNITION_TOLERANCE', '0.6'))
FACE_RECOGNITION_MODEL = os.environ.get('FACE_RECOGNITION_MODEL', 'hog')  # 'hog' or 'cnn'

# Attendance configuration
MORNING_LATE_THRESHOLD = "08:01 AM"
AFTERNOON_LATE_THRESHOLD = "01:01 PM"
MORNING_MIN_TIME = "05:00 AM"
# Lunch break: Employees can time out for lunch at any time (no time restriction)
# Afternoon time out: Employees can time out at any time (no time restriction)

# File upload configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
PHOTOS_DIR = os.path.join(BASE_DIR, 'static', 'photos')

# Session configuration
SESSION_PERMANENT = False
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security configuration
PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', '8'))
BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', '12'))
