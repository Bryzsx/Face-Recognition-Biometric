"""
Admin blueprint for dashboard, employees, attendance, reports, and settings
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from datetime import date, datetime
from utils.logger import get_logger
from utils.validators import (
    validate_required, validate_employee_registration_data, 
    validate_integer, validate_float, validate_date, validate_time,
    ValidationError, sanitize_string
)
import sqlite3
import json
import os
import base64
from io import BytesIO
from PIL import Image
import face_utils

logger = get_logger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            logger.warning("Unauthorized access attempt to admin route")
            return redirect(url_for("auth.admin_login"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        today = date.today().isoformat()

        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM employees) as total_employees,
                COALESCE(SUM(CASE WHEN date = ? AND attendance_status = 'Present' THEN 1 ELSE 0 END), 0) as present,
                COALESCE(SUM(CASE WHEN date = ? AND attendance_status = 'Absent' THEN 1 ELSE 0 END), 0) as absent,
                COALESCE(SUM(CASE WHEN date = ? AND attendance_status = 'Late' THEN 1 ELSE 0 END), 0) as late
            FROM attendance
        """, (today, today, today))
        
        stats = cur.fetchone()
        total_employees = stats[0] or 0
        present = stats[1] or 0
        absent = stats[2] or 0
        late = stats[3] or 0

        cur.execute("""
            SELECT e.full_name, e.employee_code, a.date, a.morning_in, a.lunch_out,
                   a.afternoon_in, a.time_out, a.attendance_status, a.verification_method
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            ORDER BY a.attendance_id DESC
            LIMIT 10
        """)
        recent_attendance = cur.fetchall()

        logger.info(f"Dashboard accessed by admin: {session.get('admin_name')}")
        return render_template(
            "admin/dashboard.html",
            total_employees=total_employees,
            present=present,
            absent=absent,
            late=late,
            recent_attendance=recent_attendance,
        )
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        return render_template("admin/dashboard.html", 
                             total_employees=0, present=0, absent=0, late=0, 
                             recent_attendance=[], error="Error loading dashboard")


@admin_bp.route("/register", methods=["GET", "POST"])
@admin_required
def register():
    """Register new employee"""
    if request.method == "POST":
        try:
            from app import get_db
            db = get_db()
            cur = db.cursor()

            # Validate all input data
            form_data = dict(request.form)
            validated_data, errors = validate_employee_registration_data(form_data)
            
            if errors:
                logger.warning(f"Employee registration validation errors: {errors}")
                return render_template("admin/register.html", error="; ".join(errors))

            # Handle photo saving
            photo_path = None
            face_images = validated_data.get('face_images', [])
            if face_images and len(face_images) > 0 and face_images[0]:
                try:
                    img_data = face_images[0]
                    if ',' in img_data:
                        img_data = img_data.split(',')[1]
                    
                    image_data = base64.b64decode(img_data)
                    image = Image.open(BytesIO(image_data))
                    
                    photos_dir = os.path.join('static', 'photos')
                    os.makedirs(photos_dir, exist_ok=True)
                    
                    photo_filename = f"employee_{validated_data['employee_code']}_{validated_data['full_name'].replace(' ', '_')}.jpg"
                    photo_path = os.path.join(photos_dir, photo_filename)
                    image.save(photo_path, 'JPEG', quality=85)
                    photo_path = f"photos/{photo_filename}"
                    logger.info(f"Photo saved for employee: {photo_path}")
                except Exception as e:
                    logger.warning(f"Error saving photo: {str(e)}")

            # Insert employee
            cur.execute("""
                INSERT INTO employees (
                    full_name, employee_code, address, place_of_birth, blood_type,
                    date_of_birth, gender, civil_status, age,
                    contact_number, email, course, entity_office,
                    bp_number, philhealth_number, pagibig_number, tin, id_number,
                    position, salary_grade, basic_salary, department,
                    place_of_assignment, original_place_of_assignment, item_number,
                    date_appointed, date_of_last_promotion, date_of_separation,
                    employment_status, eligibility, photo_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                validated_data['full_name'],
                validated_data['employee_code'],
                validated_data.get('address', ''),
                validated_data.get('place_of_birth', ''),
                validated_data.get('blood_type', ''),
                validated_data.get('date_of_birth'),
                validated_data.get('gender', ''),
                validated_data.get('civil_status', ''),
                validated_data.get('age'),
                validated_data.get('contact_number', ''),
                validated_data.get('email', ''),
                validated_data.get('course', ''),
                validated_data.get('entity_office', ''),
                validated_data.get('bp_number', ''),
                validated_data.get('philhealth_number', ''),
                validated_data.get('pagibig_number', ''),
                validated_data.get('tin', ''),
                validated_data.get('id_number', ''),
                validated_data.get('position', ''),
                validated_data.get('salary_grade', ''),
                validated_data.get('basic_salary'),
                validated_data.get('department', ''),
                validated_data.get('place_of_assignment', ''),
                validated_data.get('original_place_of_assignment', ''),
                validated_data.get('item_number', ''),
                validated_data.get('date_appointed'),
                validated_data.get('date_of_last_promotion'),
                validated_data.get('date_of_separation'),
                validated_data.get('employment_status', ''),
                validated_data.get('eligibility', ''),
                photo_path,
            ))

            employee_id = cur.lastrowid
            db.commit()
            logger.info(f"Employee registered successfully: ID={employee_id}, Name={validated_data['full_name']}, Code={validated_data['employee_code']}")

            # Handle face encodings
            if face_images:
                try:
                    for img_data in face_images:
                        encoding = face_utils.encode_face_from_base64(img_data)
                        if encoding is not None:
                            face_utils.save_face(employee_id, encoding)
                            logger.info(f"Face encoding saved for employee {employee_id}")
                            break
                except Exception as e:
                    logger.warning(f"Error processing face images: {str(e)}")

            return redirect(url_for("admin.employees"))

        except sqlite3.IntegrityError as e:
            db.rollback()
            error_msg = f"Employee ID '{validated_data.get('employee_code', '')}' already exists"
            logger.error(f"Registration failed - IntegrityError: {error_msg}")
            return render_template("admin/register.html", error=error_msg)
        except Exception as e:
            db.rollback()
            error_msg = f"Error: {str(e)}"
            logger.error(f"Registration error: {error_msg}", exc_info=True)
            return render_template("admin/register.html", error=error_msg)

    return render_template("admin/register.html")


@admin_bp.route("/employees")
@admin_required
def employees():
    """List all employees"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        search_query = request.args.get("search", "").strip()
        
        if search_query:
            search_pattern = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM employees 
                WHERE full_name LIKE ? OR employee_code LIKE ? OR department LIKE ?
                ORDER BY full_name
            """, (search_pattern, search_pattern, search_pattern))
        else:
            cur.execute("SELECT * FROM employees ORDER BY full_name")
        
        employees = cur.fetchall()
        logger.debug(f"Employees list accessed, found {len(employees)} employees")
        return render_template("admin/employees.html", employees=employees, search_query=search_query)
    except Exception as e:
        logger.error(f"Error in employees route: {str(e)}", exc_info=True)
        return render_template("admin/employees.html", employees=[], search_query=search_query or "")


@admin_bp.route("/employee-info")
@admin_required
def employee_info():
    """Employee information page"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        employee_id = request.args.get("id")
        
        if employee_id:
            # Try to convert to int for safety
            try:
                employee_id = int(employee_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid employee_id provided: {request.args.get('id')}")
                employee_id = None
            
            if employee_id:
                cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
                employee = cur.fetchone()
                if employee:
                    # sqlite3.Row objects use bracket notation
                    employee_name = employee["full_name"] if "full_name" in employee.keys() else "N/A"
                    logger.info(f"Employee found: ID={employee_id}, Name={employee_name}")
                    return render_template("admin/employee_info.html", employee=employee, employees=[])
                else:
                    logger.warning(f"Employee not found for ID: {employee_id}")
                    # Employee not found - show list with error message
                    cur.execute("SELECT id, full_name, employee_code, department FROM employees ORDER BY full_name")
                    employees = cur.fetchall()
                    return render_template("admin/employee_info.html", employee=None, employees=employees, error=f"Employee with ID {employee_id} not found.")
        
        # No employee_id provided - show list
        cur.execute("SELECT id, full_name, employee_code, department FROM employees ORDER BY full_name")
        employees = cur.fetchall()
        logger.debug(f"Showing employee list with {len(employees)} employees")
        return render_template("admin/employee_info.html", employee=None, employees=employees)
    except Exception as e:
        logger.error(f"Error in employee_info route: {str(e)}", exc_info=True)
        # On error, try to show the list anyway
        try:
            from db import get_db
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id, full_name, employee_code, department FROM employees ORDER BY full_name")
            employees = cur.fetchall()
            return render_template("admin/employee_info.html", employee=None, employees=employees, error=f"Error loading employee information: {str(e)}")
        except:
            return render_template("admin/employee_info.html", employee=None, employees=[], error="Error loading employee information. Please try again.")


@admin_bp.route("/employee/delete/<int:employee_id>", methods=["POST"])
@admin_required
def delete_employee(employee_id):
    """Delete an employee"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        
        # Get employee info before deletion
        cur.execute("SELECT photo_path FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        
        # Delete photo file if exists
        # sqlite3.Row objects use bracket notation, not .get()
        if employee and "photo_path" in employee.keys() and employee["photo_path"]:
            try:
                photo_path = os.path.join("static", employee["photo_path"])
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    logger.info(f"Photo deleted: {photo_path}")
            except Exception as e:
                logger.warning(f"Could not delete photo file: {str(e)}")
        
        # Delete employee and related data
        cur.execute("DELETE FROM employees WHERE id=?", (employee_id,))
        cur.execute("DELETE FROM facial_data WHERE employee_id=?", (employee_id,))
        cur.execute("DELETE FROM attendance WHERE employee_id=?", (employee_id,))
        
        db.commit()
        logger.info(f"Employee {employee_id} deleted successfully")
        return redirect(url_for("admin.employees"))
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting employee {employee_id}: {str(e)}", exc_info=True)
        return redirect(url_for("admin.employee_info", id=employee_id, error="Failed to delete employee"))


@admin_bp.route("/employee/edit/<int:employee_id>", methods=["GET", "POST"])
@admin_required
def edit_employee(employee_id):
    """Edit employee information"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        
        if request.method == "POST":
            # Validate input
            full_name = validate_required(request.form.get("full_name", "").strip(), "Full Name")
            
            # Convert optional fields
            age = validate_integer(request.form.get("age", ""), "Age", min_value=16, max_value=100)
            basic_salary = validate_float(request.form.get("basic_salary", ""), "Basic Salary", min_value=0)
            
            # Handle photo update
            photo_path = None
            face_images = request.form.get("face_images", "[]")
            if face_images and face_images != "[]":
                try:
                    images = json.loads(face_images)
                    if images and images[0]:
                        img_data = images[0]
                        if ',' in img_data:
                            img_data = img_data.split(',')[1]
                        
                        image_data = base64.b64decode(img_data)
                        image = Image.open(BytesIO(image_data))
                        
                        photos_dir = os.path.join('static', 'photos')
                        os.makedirs(photos_dir, exist_ok=True)
                        
                        cur.execute("SELECT employee_code, full_name FROM employees WHERE id=?", (employee_id,))
                        emp_data = cur.fetchone()
                        emp_code = emp_data["employee_code"] if emp_data else str(employee_id)
                        emp_name = full_name
                        
                        photo_filename = f"employee_{emp_code}_{emp_name.replace(' ', '_')}.jpg"
                        photo_path = os.path.join(photos_dir, photo_filename)
                        image.save(photo_path, 'JPEG', quality=85)
                        photo_path = f"photos/{photo_filename}"
                        logger.info(f"Photo updated for employee {employee_id}")
                except Exception as e:
                    logger.warning(f"Error saving photo: {str(e)}")
            
            # Update employee
            update_fields = [
                'full_name', 'address', 'place_of_birth', 'blood_type',
                'date_of_birth', 'gender', 'civil_status', 'age',
                'contact_number', 'email', 'course', 'entity_office',
                'bp_number', 'philhealth_number', 'pagibig_number', 'tin', 'id_number',
                'position', 'salary_grade', 'basic_salary', 'department',
                'place_of_assignment', 'original_place_of_assignment', 'item_number',
                'date_appointed', 'date_of_last_promotion', 'date_of_separation',
                'employment_status', 'eligibility'
            ]
            
            values = [
                full_name,
                sanitize_string(request.form.get("address", "")),
                sanitize_string(request.form.get("place_of_birth", "")),
                sanitize_string(request.form.get("blood_type", "")),
                validate_date(request.form.get("date_of_birth", "")),
                sanitize_string(request.form.get("gender", "")),
                sanitize_string(request.form.get("civil_status", "")),
                age,
                sanitize_string(request.form.get("contact_number", "")),
                sanitize_string(request.form.get("email", "")),
                sanitize_string(request.form.get("course", "")),
                sanitize_string(request.form.get("entity_office", "")),
                sanitize_string(request.form.get("bp_number", "")),
                sanitize_string(request.form.get("philhealth_number", "")),
                sanitize_string(request.form.get("pagibig_number", "")),
                sanitize_string(request.form.get("tin", "")),
                sanitize_string(request.form.get("id_number", "")),
                sanitize_string(request.form.get("position", "")),
                sanitize_string(request.form.get("salary_grade", "")),
                basic_salary,
                sanitize_string(request.form.get("department", "")),
                sanitize_string(request.form.get("place_of_assignment", "")),
                sanitize_string(request.form.get("original_place_of_assignment", "")),
                sanitize_string(request.form.get("item_number", "")),
                validate_date(request.form.get("date_appointed", "")),
                validate_date(request.form.get("date_of_last_promotion", "")),
                validate_date(request.form.get("date_of_separation", "")),
                sanitize_string(request.form.get("employment_status", "")),
                sanitize_string(request.form.get("eligibility", ""))
            ]
            
            if photo_path:
                update_fields.append('photo_path')
                values.append(photo_path)
            
            values.append(employee_id)
            
            placeholders = ', '.join([f"{field}=?" for field in update_fields])
            cur.execute(f"UPDATE employees SET {placeholders} WHERE id=?", values)
            
            db.commit()
            logger.info(f"Employee {employee_id} updated successfully")
            return redirect(url_for("admin.employee_info", id=employee_id))
        
        # GET request - show edit form
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        if not employee:
            return redirect(url_for("admin.employees"))
        
        return render_template("admin/edit_employee.html", employee=employee)
        
    except ValidationError as e:
        logger.warning(f"Validation error editing employee {employee_id}: {str(e)}")
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        return render_template("admin/edit_employee.html", employee=employee, error=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating employee {employee_id}: {str(e)}", exc_info=True)
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        return render_template("admin/edit_employee.html", employee=employee, error=str(e))


@admin_bp.route("/attendance")
@admin_required
def attendance():
    """Attendance management page"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        
        selected_date = request.args.get("date", date.today().isoformat())
        
        cur.execute("""
            SELECT a.attendance_id, e.id, e.full_name, a.date, a.morning_in, a.lunch_out, 
                   a.afternoon_in, a.time_out, a.attendance_status
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.date=?
            ORDER BY e.full_name
        """, (selected_date,))

        records = cur.fetchall()
        return render_template("admin/attendance.html", records=records, selected_date=selected_date)
    except Exception as e:
        logger.error(f"Error in attendance route: {str(e)}", exc_info=True)
        return render_template("admin/attendance.html", records=[], selected_date=date.today().isoformat())


@admin_bp.route("/attendance/edit/<int:attendance_id>", methods=["GET", "POST"])
@admin_required
def edit_dtr(attendance_id):
    """Edit Daily Time Record"""
    try:
        from db import get_db
        from utils.helpers import check_if_late
        db = get_db()
        cur = db.cursor()
        
        if request.method == "POST":
            # Get form data
            if request.is_json:
                data = request.get_json()
                morning_in = data.get("morning_in", "").strip() or None
                lunch_out = data.get("lunch_out", "").strip() or None
                afternoon_in = data.get("afternoon_in", "").strip() or None
                time_out = data.get("time_out", "").strip() or None
                attendance_date = validate_required(data.get("date", ""), "Date")
            else:
                morning_in = validate_time(request.form.get("morning_in", ""), "Morning In") if request.form.get("morning_in") else None
                lunch_out = validate_time(request.form.get("lunch_out", ""), "Lunch Out") if request.form.get("lunch_out") else None
                afternoon_in = validate_time(request.form.get("afternoon_in", ""), "Afternoon In") if request.form.get("afternoon_in") else None
                time_out = validate_time(request.form.get("time_out", ""), "Time Out") if request.form.get("time_out") else None
                attendance_date = validate_required(request.form.get("date", ""), "Date")
            
            # Get existing record
            cur.execute("SELECT * FROM attendance WHERE attendance_id=?", (attendance_id,))
            existing = cur.fetchone()
            
            if not existing:
                if request.is_json:
                    return jsonify({"success": False, "message": "Attendance record not found"}), 404
                return redirect(url_for("admin.attendance"))
            
            # Determine attendance status
            attendance_status = "Present"
            if morning_in:
                try:
                    if check_if_late(morning_in, "morning"):
                        attendance_status = "Late"
                except:
                    pass
            
            if afternoon_in:
                try:
                    if attendance_status != "Late" and check_if_late(afternoon_in, "afternoon"):
                        attendance_status = "Late"
                except:
                    pass
            
            # Update attendance record
            cur.execute("""
                UPDATE attendance 
                SET morning_in=?, lunch_out=?, afternoon_in=?, time_out=?, 
                    attendance_status=?, date=?
                WHERE attendance_id=?
            """, (morning_in, lunch_out, afternoon_in, time_out, attendance_status, attendance_date, attendance_id))
            
            db.commit()
            logger.info(f"DTR {attendance_id} updated successfully")
            
            if request.is_json:
                return jsonify({"success": True, "message": "DTR updated successfully"})
            return redirect(url_for("admin.attendance", date=attendance_date))
        
        # GET request
        cur.execute("""
            SELECT a.*, e.full_name, e.employee_code
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.attendance_id=?
        """, (attendance_id,))
        
        record = cur.fetchone()
        
        if not record:
            return redirect(url_for("admin.attendance"))
        
        return render_template("admin/edit_dtr.html", record=record)
        
    except ValidationError as e:
        logger.warning(f"Validation error editing DTR {attendance_id}: {str(e)}")
        if request.is_json:
            return jsonify({"success": False, "message": str(e)}), 400
        cur.execute("SELECT a.*, e.full_name, e.employee_code FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.attendance_id=?", (attendance_id,))
        record = cur.fetchone()
        return render_template("admin/edit_dtr.html", record=record, error=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating DTR {attendance_id}: {str(e)}", exc_info=True)
        if request.is_json:
            return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
        cur.execute("SELECT a.*, e.full_name, e.employee_code FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.attendance_id=?", (attendance_id,))
        record = cur.fetchone()
        return render_template("admin/edit_dtr.html", record=record, error=str(e))


@admin_bp.route("/reports")
@admin_required
def reports():
    """Reports/DTR generation page"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        
        cur.execute("SELECT id, full_name, employee_code FROM employees ORDER BY full_name")
        employees = cur.fetchall()
        
        employee_id = request.args.get("employee_id")
        month_year = request.args.get("month", "")
        
        dtr_data = None
        employee_info = None
        
        if employee_id and month_year:
            cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
            employee_info = cur.fetchone()
            
            try:
                year, month = month_year.split("-")
                cur.execute("""
                    SELECT date, morning_in, lunch_out, afternoon_in, time_out, attendance_status
                    FROM attendance
                    WHERE employee_id=? AND date LIKE ?
                    ORDER BY date
                """, (employee_id, f"{year}-{month}-%"))
                
                attendance_records = cur.fetchall()
                
                dtr_data = {
                    "year": year,
                    "month": month,
                    "records": {}
                }
                
                for record in attendance_records:
                    day = record["date"].split("-")[2]
                    dtr_data["records"][day] = {
                        "morning_in": record["morning_in"] or "",
                        "lunch_out": record["lunch_out"] or "",
                        "afternoon_in": record["afternoon_in"] or "",
                        "time_out": record["time_out"] or "",
                        "status": record["attendance_status"] or ""
                    }
            except Exception as e:
                logger.warning(f"Error processing DTR data: {str(e)}")
        
        return render_template(
            "admin/reports.html",
            employees=employees,
            employee_id=employee_id,
            month_year=month_year,
            dtr_data=dtr_data,
            employee_info=employee_info
        )
    except Exception as e:
        logger.error(f"Error in reports route: {str(e)}", exc_info=True)
        return render_template("admin/reports.html", employees=[], dtr_data=None, employee_info=None)


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    """Settings page for holidays and suspensions"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        
        if request.method == "POST":
            action = request.form.get("action")
            
            if action == "mark_holiday":
                holiday_date = validate_required(request.form.get("holiday_date", ""), "Holiday Date")
                reason = sanitize_string(request.form.get("reason", "Holiday"), max_length=200) or "Holiday"
                
                cur.execute("SELECT id FROM employees WHERE status='Active'")
                employees = cur.fetchall()
                
                if not employees:
                    return render_template("admin/settings.html", 
                                         error="No active employees found",
                                         success=None)
                
                marked_count = 0
                for emp in employees:
                    employee_id = emp["id"]
                    
                    cur.execute("""
                        SELECT attendance_id FROM attendance 
                        WHERE employee_id=? AND date=?
                    """, (employee_id, holiday_date))
                    existing = cur.fetchone()
                    
                    if existing:
                        cur.execute("""
                            UPDATE attendance 
                            SET morning_in='08:00 AM', 
                                lunch_out='12:00 PM',
                                afternoon_in='01:00 PM',
                                time_out='05:00 PM',
                                attendance_status='Present',
                                verification_method=?
                            WHERE employee_id=? AND date=?
                        """, (f"Admin: {reason}", employee_id, holiday_date))
                    else:
                        cur.execute("""
                            INSERT INTO attendance 
                            (employee_id, date, morning_in, lunch_out, afternoon_in, 
                             time_out, attendance_status, verification_method)
                            VALUES (?, ?, '08:00 AM', '12:00 PM', '01:00 PM', 
                                    '05:00 PM', 'Present', ?)
                        """, (employee_id, holiday_date, f"Admin: {reason}"))
                    
                    marked_count += 1
                
                db.commit()
                logger.info(f"Holiday marked for {marked_count} employees on {holiday_date}")
                return render_template("admin/settings.html",
                                     success=f"Successfully marked {marked_count} employees as present for {holiday_date} ({reason})",
                                     error=None)
            
            elif action == "mark_suspension":
                suspension_date = validate_required(request.form.get("suspension_date", ""), "Suspension Date")
                reason = sanitize_string(request.form.get("reason", "Suspension"), max_length=200) or "Suspension"
                
                cur.execute("SELECT id FROM employees WHERE status='Active'")
                employees = cur.fetchall()
                
                if not employees:
                    return render_template("admin/settings.html",
                                         error="No active employees found",
                                         success=None)
                
                marked_count = 0
                for emp in employees:
                    employee_id = emp["id"]
                    
                    cur.execute("""
                        SELECT attendance_id FROM attendance 
                        WHERE employee_id=? AND date=?
                    """, (employee_id, suspension_date))
                    existing = cur.fetchone()
                    
                    if existing:
                        cur.execute("""
                            UPDATE attendance 
                            SET morning_in='08:00 AM', 
                                lunch_out='12:00 PM',
                                afternoon_in='01:00 PM',
                                time_out='05:00 PM',
                                attendance_status='Present',
                                verification_method=?
                            WHERE employee_id=? AND date=?
                        """, (f"Admin: {reason}", employee_id, suspension_date))
                    else:
                        cur.execute("""
                            INSERT INTO attendance 
                            (employee_id, date, morning_in, lunch_out, afternoon_in, 
                             time_out, attendance_status, verification_method)
                            VALUES (?, ?, '08:00 AM', '12:00 PM', '01:00 PM', 
                                    '05:00 PM', 'Present', ?)
                        """, (employee_id, suspension_date, f"Admin: {reason}"))
                    
                    marked_count += 1
                
                db.commit()
                logger.info(f"Suspension marked for {marked_count} employees on {suspension_date}")
                return render_template("admin/settings.html",
                                     success=f"Successfully marked {marked_count} employees as present for {suspension_date} ({reason})",
                                     error=None)
        
        return render_template("admin/settings.html", error=None, success=None)
        
    except ValidationError as e:
        logger.warning(f"Validation error in settings: {str(e)}")
        return render_template("admin/settings.html", error=str(e), success=None)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in settings: {str(e)}", exc_info=True)
        return render_template("admin/settings.html",
                             error=f"Error: {str(e)}",
                             success=None)


@admin_bp.route("/capture-face", methods=["POST"])
@admin_required
def capture_face():
    """Endpoint to capture and encode a single face image"""
    try:
        data = request.get_json()
        image_data = data.get("image")
        employee_id = data.get("employee_id")

        if not image_data:
            return jsonify({"success": False, "error": "No image data provided"}), 400

        encoding = face_utils.encode_face_from_base64(image_data)
        
        if encoding is None:
            return jsonify({"success": False, "error": "No face detected in image"}), 400

        if employee_id:
            face_utils.save_face(employee_id, encoding)
            logger.info(f"Face captured and saved for employee {employee_id}")

        return jsonify({"success": True, "message": "Face captured successfully"})
    except Exception as e:
        logger.error(f"Error capturing face: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
