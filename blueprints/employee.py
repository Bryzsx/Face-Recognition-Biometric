"""
Employee blueprint for employee-facing pages
"""
from flask import Blueprint, render_template
from utils.logger import get_logger

logger = get_logger(__name__)
employee_bp = Blueprint('employee', __name__)


@employee_bp.route("/attendance")
def attendance():
    """Main page for employees to scan their face for attendance"""
    logger.info("Employee attendance page accessed")
    return render_template("employee_attendance.html")
