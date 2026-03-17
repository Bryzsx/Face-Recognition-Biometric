import os
import secrets

import bcrypt

from config import BCRYPT_LOG_ROUNDS, PASSWORD_MIN_LENGTH
from utils.logger import get_logger
from utils.validators import ValidationError


logger = get_logger(__name__)


# ========================= PASSWORD HELPERS =========================

def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    if not plain_password:
        raise ValueError("Password cannot be empty")
    if len(plain_password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")

    rounds = max(4, min(BCRYPT_LOG_ROUNDS, 14))
    salt = bcrypt.gensalt(rounds)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.
    Falls back to simple string comparison if stored password is not a bcrypt hash
    (for backward compatibility with existing plain-text passwords).
    """
    if not hashed_password:
        return False

    # If value does not look like a bcrypt hash, do a direct comparison
    if not hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        return plain_password == hashed_password

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.error(f"Error verifying password: {exc}", exc_info=True)
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Determine if a stored bcrypt hash should be rehashed
    (e.g., when rounds setting changes).
    """
    if not hashed_password or not hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        # Plain-text or unknown format - should be upgraded
        return True
    try:
        parts = hashed_password.split("$")
        if len(parts) < 3:
            return True
        cost_str = parts[2]
        current_cost = int(cost_str)
        desired_cost = max(4, min(BCRYPT_LOG_ROUNDS, 14))
        return current_cost != desired_cost
    except Exception:
        return True


# ========================= CSRF HELPERS =========================

def generate_csrf_token():
    """
    Generate or return the current CSRF token stored in the session.
    Exposed to templates via the `csrf_token()` context processor.
    """
    from flask import session

    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf_token():
    """
    Validate CSRF token for non-JSON POST requests.
    Raises ValidationError if the token is missing or invalid.
    """
    from flask import request, session

    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return

    if request.is_json:
        # JSON APIs are handled separately if needed
        return

    token = None
    if request.form:
        token = request.form.get("_csrf_token")

    if not token:
        # Fallback to header (for programmatic clients)
        token = request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")

    if not token or token != session.get("_csrf_token"):
        raise ValidationError("Invalid or missing CSRF token.")
