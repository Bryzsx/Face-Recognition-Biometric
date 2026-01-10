"""
Authentication blueprint for login/logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from utils.logger import get_logger
from utils.validators import validate_required, ValidationError

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        try:
            username = validate_required(request.form.get("username"), "Username")
            password = validate_required(request.form.get("password"), "Password")
            
            from db import get_db
            db = get_db()
            cur = db.cursor()
            cur.execute(
                "SELECT * FROM admin WHERE username=? AND password=?",
                (username, password),
            )
            admin = cur.fetchone()

            if admin:
                session["admin_logged_in"] = True
                session["admin_name"] = admin["name"]
                logger.info(f"Admin login successful: {username}")
                return redirect(url_for("admin.dashboard"))

            logger.warning(f"Failed login attempt for username: {username}")
            return render_template("admin_login.html", error="Invalid login")

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
