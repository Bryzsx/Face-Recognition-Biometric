"""
Authentication blueprint for login/logout
"""
import time

from flask import Blueprint, render_template, request, redirect, url_for, session
from utils.logger import get_logger
from utils.validators import validate_required, ValidationError
from utils.security import (
    verify_password,
    needs_rehash,
    hash_password,
)

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        try:
            # Simple rate limiting per session to slow brute-force attacks
            lock_until = session.get("login_lock_until")
            now = time.time()
            if lock_until and now < lock_until:
                remaining = int(lock_until - now)
                minutes = max(1, remaining // 60)
                return render_template(
                    "admin_login.html",
                    error=f"Too many failed attempts. Please wait {minutes} minute(s) before trying again.",
                    lock_remaining=remaining,
                )

            username = validate_required(request.form.get("username"), "Username")
            password = validate_required(request.form.get("password"), "Password")
            
            from db import get_db
            db = get_db()
            cur = db.cursor()
            cur.execute(
                "SELECT * FROM admin WHERE username=?",
                (username,),
            )
            admin = cur.fetchone()

            # Verify password (supports both old plain-text and new bcrypt hashes)
            if admin and verify_password(password, admin["password"]):
                # Optionally upgrade weak/plain hashes transparently
                try:
                    if needs_rehash(admin["password"]):
                        new_hash = hash_password(password)
                        cur.execute(
                            "UPDATE admin SET password=? WHERE id=?",
                            (new_hash, admin["id"]),
                        )
                        db.commit()
                except Exception as upgrade_exc:
                    logger.warning(f"Could not upgrade admin password hash: {upgrade_exc}")

                # Successful login: clear rate-limit state
                session.pop("login_attempts", None)
                session.pop("login_lock_until", None)

                session["admin_logged_in"] = True
                session["admin_name"] = admin["name"]
                session["admin_id"] = admin["id"]
                try:
                    session["admin_photo_path"] = (admin["photo_path"] or "") if "photo_path" in admin.keys() else ""
                except Exception:
                    session["admin_photo_path"] = ""
                logger.info(f"Admin login successful: {username}")
                return redirect(url_for("admin.dashboard"))

            # Failed login: only count attempts and lock for wrong password (not for non-existent account)
            if not admin:
                logger.warning(f"Login attempt for non-existent username: {username}")
                return render_template(
                    "admin_login.html",
                    error="This account does not exist.",
                )

            attempts = session.get("login_attempts", 0) + 1
            session["login_attempts"] = attempts
            if attempts >= 5:
                # Lock for 3 minutes after 5 wrong-password attempts
                session["login_lock_until"] = time.time() + 3 * 60
                logger.warning(f"Too many failed login attempts for username: {username}")
                return render_template(
                    "admin_login.html",
                    error="Too many failed attempts. Please wait 3 minutes before trying again.",
                    lock_remaining=3 * 60,
                )

            logger.warning(f"Failed login attempt for username: {username} (attempt {attempts}/5)")
            return render_template(
                "admin_login.html",
                error=f"Invalid password. (attempt {attempts} of 5).",
            )

        except ValidationError as e:
            logger.warning(f"Login validation error: {str(e)}")
            return render_template("admin_login.html", error=str(e))
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return render_template("admin_login.html", error="An error occurred. Please try again.")

    return render_template("admin_login.html")


@auth_bp.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    admin_name = session.get("admin_name", "Unknown")
    session.clear()
    logger.info(f"Admin logout: {admin_name}")
    return redirect(url_for("auth.admin_login"))
