from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
from functools import wraps
from datetime import date
import json
import face_utils
import os
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.secret_key = "super-secret-key"
DATABASE = "biometric.db"


# ================= DATABASE =================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ================= AUTH DECORATOR =================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper
#================= SERVER HEADER =================
@app.after_request
def hide_server_header(response):
    response.headers['Server'] = 'SecureServer'
    return response


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

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
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", error="Invalid login")

    return render_template("admin_login.html")


# ================= LOGOUT =================
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ================= DASHBOARD =================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    cur = db.cursor()
    today = date.today().isoformat()

    cur.execute("SELECT COUNT(*) FROM employees")
    total_employees = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=? AND attendance_status='Present'",
        (today,),
    )
    present = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=? AND attendance_status='Absent'",
        (today,),
    )
    absent = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=? AND attendance_status='Late'",
        (today,),
    )
    late = cur.fetchone()[0]

    # Get recent attendance records (last 10 records)
    cur.execute("""
        SELECT e.full_name, e.employee_code, a.date, a.morning_in, a.lunch_out,
               a.afternoon_in, a.time_out, a.attendance_status, a.verification_method
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        ORDER BY a.date DESC, a.morning_in DESC
        LIMIT 10
    """)
    recent_attendance = cur.fetchall()

    return render_template(
        "admin/dashboard.html",
        total_employees=total_employees,
        present=present,
        absent=absent,
        late=late,
        recent_attendance=recent_attendance,
    )


# ================= REGISTER =================
@app.route("/admin/register", methods=["GET", "POST"])
@admin_required
def admin_register():
    if request.method == "POST":
        # Debug: Print received form data
        print("\n" + "="*50)
        print("REGISTRATION ATTEMPT")
        print("="*50)
        print(f"Form data keys: {list(request.form.keys())}")
        print(f"Full Name: {request.form.get('full_name', 'NOT PROVIDED')}")
        print(f"Employee ID: {request.form.get('employee_id', 'NOT PROVIDED')}")
        print("="*50 + "\n")
        
        db = get_db()
        cur = db.cursor()

        try:
            # Validate required fields
            full_name = request.form.get("full_name", "").strip()
            employee_code = request.form.get("employee_id", "").strip()
            
            if not full_name:
                return render_template("admin/register.html", error="Full Name is required")
            if not employee_code:
                return render_template("admin/register.html", error="Employee ID is required")
            
            # Convert age to int if provided
            age_str = request.form.get("age", "")
            age = int(age_str) if age_str and age_str.isdigit() else None
            
            # Convert basic_salary to float if provided
            salary_str = request.form.get("basic_salary", "")
            basic_salary = float(salary_str) if salary_str and salary_str.replace('.', '').isdigit() else None
            
            # Handle photo saving first
            photo_path = None
            face_images = request.form.get("face_images", "[]")
            if face_images and face_images != "[]":
                try:
                    images = json.loads(face_images)
                    if images and images[0]:
                        # Save the first image as employee photo
                        img_data = images[0]
                        # Remove data URL prefix if present
                        if ',' in img_data:
                            img_data = img_data.split(',')[1]
                        
                        # Decode and save image
                        image_data = base64.b64decode(img_data)
                        image = Image.open(BytesIO(image_data))
                        
                        # Create photos directory if it doesn't exist
                        photos_dir = os.path.join('static', 'photos')
                        os.makedirs(photos_dir, exist_ok=True)
                        
                        # Save photo with employee ID as filename
                        photo_filename = f"employee_{employee_code}_{full_name.replace(' ', '_')}.jpg"
                        photo_path = os.path.join(photos_dir, photo_filename)
                        image.save(photo_path, 'JPEG', quality=85)
                        photo_path = f"photos/{photo_filename}"  # Relative path for URL
                        print(f"✅ Photo saved: {photo_path}")
                except Exception as e:
                    print(f"⚠️  Error saving photo: {e}")
            
            # Insert employee with all fields including photo_path
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
                full_name,
                employee_code,
                request.form.get("address", "").strip(),
                request.form.get("place_of_birth", "").strip(),
                request.form.get("blood_type", "").strip(),
                request.form.get("date_of_birth", "").strip(),
                request.form.get("gender", "").strip(),
                request.form.get("civil_status", "").strip(),
                age,
                request.form.get("contact_number", "").strip(),
                request.form.get("email", "").strip(),
                request.form.get("course", "").strip(),
                request.form.get("entity_office", "").strip(),
                request.form.get("bp_number", "").strip(),
                request.form.get("philhealth_number", "").strip(),
                request.form.get("pagibig_number", "").strip(),
                request.form.get("tin", "").strip(),
                request.form.get("id_number", "").strip(),
                request.form.get("position", "").strip(),
                request.form.get("salary_grade", "").strip(),
                basic_salary,
                request.form.get("department", "").strip(),
                request.form.get("place_of_assignment", "").strip(),
                request.form.get("original_place_of_assignment", "").strip(),
                request.form.get("item_number", "").strip(),
                request.form.get("date_appointed", "").strip(),
                request.form.get("date_of_last_promotion", "").strip(),
                request.form.get("date_of_separation", "").strip(),
                request.form.get("employment_status", "").strip(),
                request.form.get("eligibility", "").strip(),
                photo_path,
            ))

            employee_id = cur.lastrowid
            db.commit()
            print(f"✅ Employee registered successfully: ID={employee_id}, Name={full_name}, Code={employee_code}")

            # Handle face encodings if provided
            if face_images and face_images != "[]":
                try:
                    images = json.loads(face_images)
                    if images:
                        # Encode and save the first valid face
                        for img_data in images:
                            encoding = face_utils.encode_face_from_base64(img_data)
                            if encoding is not None:
                                face_utils.save_face(employee_id, encoding)
                                print(f"✅ Face encoding saved for employee {employee_id}")
                                break  # Save only the first valid encoding
                except Exception as e:
                    print(f"⚠️  Error processing face images: {e}")

            return redirect(url_for("admin_employees"))
        except sqlite3.IntegrityError as e:
            db.rollback()
            error_msg = f"Employee ID '{employee_code}' already exists" if 'employee_code' in locals() else "Employee ID already exists"
            print(f"❌ Registration failed: {error_msg}")
            return render_template("admin/register.html", error=error_msg)
        except Exception as e:
            db.rollback()
            error_msg = f"Error: {str(e)}"
            print(f"❌ Registration error: {error_msg}")
            import traceback
            traceback.print_exc()
            return render_template("admin/register.html", error=error_msg)

    return render_template("admin/register.html")


# ================= FACE CAPTURE =================
@app.route("/admin/capture-face", methods=["POST"])
@admin_required
def capture_face():
    """Endpoint to capture and encode a single face image"""
    try:
        data = request.get_json()
        image_data = data.get("image")
        employee_id = data.get("employee_id")

        if not image_data:
            return jsonify({"success": False, "error": "No image data provided"}), 400

        # Encode face from base64
        encoding = face_utils.encode_face_from_base64(image_data)
        
        if encoding is None:
            return jsonify({"success": False, "error": "No face detected in image"}), 400

        # If employee_id is provided, save it
        if employee_id:
            face_utils.save_face(employee_id, encoding)

        return jsonify({"success": True, "message": "Face captured successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ================= EMPLOYEES =================
@app.route("/admin/employees")
@admin_required
def admin_employees():
    db = get_db()
    cur = db.cursor()
    search_query = request.args.get("search", "").strip()
    
    try:
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
        return render_template("admin/employees.html", employees=employees, search_query=search_query)
    except Exception as e:
        print(f"Error in admin_employees route: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list on error
        return render_template("admin/employees.html", employees=[], search_query=search_query or "")


# ================= EMPLOYEE INFO =================
@app.route("/admin/employee-info")
@admin_required
def admin_employee_info():
    db = get_db()
    cur = db.cursor()
    employee_id = request.args.get("id")
    
    if employee_id:
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        if employee:
            return render_template("admin/employee_info.html", employee=employee, employees=None)
        # If employee not found, fall through to show list
    
    # If no employee selected or employee not found, show employee list
    cur.execute("SELECT id, full_name, employee_code, department FROM employees ORDER BY full_name")
    employees = cur.fetchall()
    return render_template("admin/employee_info.html", employees=employees, employee=None)


# ================= DELETE EMPLOYEE =================
@app.route("/admin/employee/delete/<int:employee_id>", methods=["POST"])
@admin_required
def delete_employee(employee_id):
    db = get_db()
    cur = db.cursor()
    
    try:
        # Get employee info before deletion (for photo cleanup)
        cur.execute("SELECT photo_path FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        
        # Delete photo file if exists
        if employee:
            try:
                # sqlite3.Row objects use bracket notation, check if key exists first
                if "photo_path" in employee.keys() and employee["photo_path"]:
                    photo_path = os.path.join("static", employee["photo_path"])
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
            except (KeyError, TypeError, Exception) as e:
                print(f"Warning: Could not delete photo file: {e}")
        
        # Delete employee
        cur.execute("DELETE FROM employees WHERE id=?", (employee_id,))
        
        # Delete associated face encoding
        cur.execute("DELETE FROM facial_data WHERE employee_id=?", (employee_id,))
        
        # Delete attendance records
        cur.execute("DELETE FROM attendance WHERE employee_id=?", (employee_id,))
        
        db.commit()
        print(f"✅ Employee {employee_id} deleted successfully")
        return redirect(url_for("admin_employees"))
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting employee: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for("admin_employee_info", id=employee_id, error="Failed to delete employee"))


# ================= EDIT EMPLOYEE =================
@app.route("/admin/employee/edit/<int:employee_id>", methods=["GET", "POST"])
@admin_required
def edit_employee(employee_id):
    db = get_db()
    cur = db.cursor()
    
    if request.method == "POST":
        try:
            # Validate required fields
            full_name = request.form.get("full_name", "").strip()
            if not full_name:
                cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
                employee = cur.fetchone()
                return render_template("admin/edit_employee.html", employee=employee, error="Full Name is required")
            
            # Convert age to int if provided
            age_str = request.form.get("age", "")
            age = int(age_str) if age_str and age_str.isdigit() else None
            
            # Convert basic_salary to float if provided
            salary_str = request.form.get("basic_salary", "")
            basic_salary = float(salary_str) if salary_str and salary_str.replace('.', '').isdigit() else None
            
            # Handle photo update if new photo provided
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
                        
                        # Get employee code for filename
                        cur.execute("SELECT employee_code, full_name FROM employees WHERE id=?", (employee_id,))
                        emp_data = cur.fetchone()
                        emp_code = emp_data["employee_code"] if emp_data else str(employee_id)
                        emp_name = emp_data["full_name"] if emp_data else "Employee"
                        
                        photo_filename = f"employee_{emp_code}_{emp_name.replace(' ', '_')}.jpg"
                        photo_path = os.path.join(photos_dir, photo_filename)
                        image.save(photo_path, 'JPEG', quality=85)
                        photo_path = f"photos/{photo_filename}"
                except Exception as e:
                    print(f"⚠️  Error saving photo: {e}")
            
            # Update employee - only update photo_path if new photo provided
            if photo_path:
                cur.execute("""
                    UPDATE employees SET
                        full_name=?, address=?, place_of_birth=?, blood_type=?,
                        date_of_birth=?, gender=?, civil_status=?, age=?,
                        contact_number=?, email=?, course=?, entity_office=?,
                        bp_number=?, philhealth_number=?, pagibig_number=?, tin=?, id_number=?,
                        position=?, salary_grade=?, basic_salary=?, department=?,
                        place_of_assignment=?, original_place_of_assignment=?, item_number=?,
                        date_appointed=?, date_of_last_promotion=?, date_of_separation=?,
                        employment_status=?, eligibility=?, photo_path=?
                    WHERE id=?
                """, (
                    full_name,
                    request.form.get("address", "").strip(),
                    request.form.get("place_of_birth", "").strip(),
                    request.form.get("blood_type", "").strip(),
                    request.form.get("date_of_birth", "").strip(),
                    request.form.get("gender", "").strip(),
                    request.form.get("civil_status", "").strip(),
                    age,
                    request.form.get("contact_number", "").strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("course", "").strip(),
                    request.form.get("entity_office", "").strip(),
                    request.form.get("bp_number", "").strip(),
                    request.form.get("philhealth_number", "").strip(),
                    request.form.get("pagibig_number", "").strip(),
                    request.form.get("tin", "").strip(),
                    request.form.get("id_number", "").strip(),
                    request.form.get("position", "").strip(),
                    request.form.get("salary_grade", "").strip(),
                    basic_salary,
                    request.form.get("department", "").strip(),
                    request.form.get("place_of_assignment", "").strip(),
                    request.form.get("original_place_of_assignment", "").strip(),
                    request.form.get("item_number", "").strip(),
                    request.form.get("date_appointed", "").strip(),
                    request.form.get("date_of_last_promotion", "").strip(),
                    request.form.get("date_of_separation", "").strip(),
                    request.form.get("employment_status", "").strip(),
                    request.form.get("eligibility", "").strip(),
                    photo_path,
                    employee_id,
                ))
            else:
                cur.execute("""
                    UPDATE employees SET
                        full_name=?, address=?, place_of_birth=?, blood_type=?,
                        date_of_birth=?, gender=?, civil_status=?, age=?,
                        contact_number=?, email=?, course=?, entity_office=?,
                        bp_number=?, philhealth_number=?, pagibig_number=?, tin=?, id_number=?,
                        position=?, salary_grade=?, basic_salary=?, department=?,
                        place_of_assignment=?, original_place_of_assignment=?, item_number=?,
                        date_appointed=?, date_of_last_promotion=?, date_of_separation=?,
                        employment_status=?, eligibility=?
                    WHERE id=?
                """, (
                    full_name,
                    request.form.get("address", "").strip(),
                    request.form.get("place_of_birth", "").strip(),
                    request.form.get("blood_type", "").strip(),
                    request.form.get("date_of_birth", "").strip(),
                    request.form.get("gender", "").strip(),
                    request.form.get("civil_status", "").strip(),
                    age,
                    request.form.get("contact_number", "").strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("course", "").strip(),
                    request.form.get("entity_office", "").strip(),
                    request.form.get("bp_number", "").strip(),
                    request.form.get("philhealth_number", "").strip(),
                    request.form.get("pagibig_number", "").strip(),
                    request.form.get("tin", "").strip(),
                    request.form.get("id_number", "").strip(),
                    request.form.get("position", "").strip(),
                    request.form.get("salary_grade", "").strip(),
                    basic_salary,
                    request.form.get("department", "").strip(),
                    request.form.get("place_of_assignment", "").strip(),
                    request.form.get("original_place_of_assignment", "").strip(),
                    request.form.get("item_number", "").strip(),
                    request.form.get("date_appointed", "").strip(),
                    request.form.get("date_of_last_promotion", "").strip(),
                    request.form.get("date_of_separation", "").strip(),
                    request.form.get("employment_status", "").strip(),
                    request.form.get("eligibility", "").strip(),
                    employee_id,
                ))
            
            db.commit()
            print(f"✅ Employee {employee_id} updated successfully")
            return redirect(url_for("admin_employee_info", id=employee_id))
        except Exception as e:
            db.rollback()
            print(f"❌ Error updating employee: {e}")
            import traceback
            traceback.print_exc()
            return render_template("admin/edit_employee.html", employee=employee, error=str(e))
    
    # GET request - show edit form
    cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
    employee = cur.fetchone()
    if not employee:
        return redirect(url_for("admin_employees"))
    
    return render_template("admin/edit_employee.html", employee=employee)


# ================= ATTENDANCE =================
@app.route("/admin/attendance")
@admin_required
def admin_attendance():
    db = get_db()
    cur = db.cursor()
    
    # Get selected date or use today
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


# ================= EDIT DTR =================
@app.route("/admin/attendance/edit/<int:attendance_id>", methods=["GET", "POST"])
@admin_required
def edit_dtr(attendance_id):
    """Edit Daily Time Record for an employee"""
    db = get_db()
    cur = db.cursor()
    
    if request.method == "POST":
        try:
            # Get form data (handle both JSON and form data)
            if request.is_json:
                data = request.get_json()
                morning_in = data.get("morning_in", "").strip() or None
                lunch_out = data.get("lunch_out", "").strip() or None
                afternoon_in = data.get("afternoon_in", "").strip() or None
                time_out = data.get("time_out", "").strip() or None
                attendance_date = data.get("date", "").strip()
            else:
                morning_in = request.form.get("morning_in", "").strip() or None
                lunch_out = request.form.get("lunch_out", "").strip() or None
                afternoon_in = request.form.get("afternoon_in", "").strip() or None
                time_out = request.form.get("time_out", "").strip() or None
                attendance_date = request.form.get("date", "").strip()
            
            # Validate date
            if not attendance_date:
                if request.is_json:
                    return jsonify({"success": False, "message": "Date is required"}), 400
                else:
                    cur.execute("SELECT a.*, e.full_name, e.employee_code FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.attendance_id=?", (attendance_id,))
                    record = cur.fetchone()
                    return render_template("admin/edit_dtr.html", record=record, error="Date is required")
            
            # Get existing record
            cur.execute("SELECT * FROM attendance WHERE attendance_id=?", (attendance_id,))
            existing = cur.fetchone()
            
            if not existing:
                if request.is_json:
                    return jsonify({"success": False, "message": "Attendance record not found"}), 404
                else:
                    return redirect(url_for("admin_attendance"))
            
            # Determine attendance status based on times
            attendance_status = "Present"
            
            # Check if morning time is late
            if morning_in:
                try:
                    from datetime import datetime
                    morning_time = datetime.strptime(morning_in, "%I:%M %p")
                    late_threshold = datetime.strptime("08:30 AM", "%I:%M %p")
                    if morning_time >= late_threshold:
                        attendance_status = "Late"
                except:
                    pass
            
            # Check if afternoon time is late
            if afternoon_in and attendance_status == "Present":
                try:
                    from datetime import datetime
                    afternoon_time = datetime.strptime(afternoon_in, "%I:%M %p")
                    late_threshold = datetime.strptime("01:30 PM", "%I:%M %p")
                    if afternoon_time >= late_threshold:
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
            
            if request.is_json:
                return jsonify({
                    "success": True,
                    "message": "DTR updated successfully"
                })
            else:
                return redirect(url_for("admin_attendance", date=attendance_date))
            
        except Exception as e:
            db.rollback()
            print(f"Error updating DTR: {e}")
            import traceback
            traceback.print_exc()
            if request.is_json:
                return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
            else:
                cur.execute("SELECT a.*, e.full_name, e.employee_code FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.attendance_id=?", (attendance_id,))
                record = cur.fetchone()
                return render_template("admin/edit_dtr.html", record=record, error=f"Error: {str(e)}")
    
    # GET request - show edit form
    cur.execute("""
        SELECT a.*, e.full_name, e.employee_code
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.attendance_id=?
    """, (attendance_id,))
    
    record = cur.fetchone()
    
    if not record:
        return redirect(url_for("admin_attendance"))
    
    return render_template("admin/edit_dtr.html", record=record)


# ================= REPORTS =================
@app.route("/admin/reports")
@admin_required
def admin_reports():
    db = get_db()
    cur = db.cursor()
    
    # Get employee list for dropdown
    cur.execute("SELECT id, full_name, employee_code FROM employees ORDER BY full_name")
    employees = cur.fetchall()
    
    # Get selected employee and month
    employee_id = request.args.get("employee_id")
    month_year = request.args.get("month", "")
    
    dtr_data = None
    employee_info = None
    
    if employee_id and month_year:
        # Get employee info
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee_info = cur.fetchone()
        
        # Parse month and year
        try:
            year, month = month_year.split("-")
            # Get all attendance records for the selected month
            cur.execute("""
                SELECT date, morning_in, lunch_out, afternoon_in, time_out, attendance_status
                FROM attendance
                WHERE employee_id=? AND date LIKE ?
                ORDER BY date
            """, (employee_id, f"{year}-{month}-%"))
            
            attendance_records = cur.fetchall()
            
            # Build DTR data structure
            dtr_data = {
                "year": year,
                "month": month,
                "records": {}
            }
            
            # Convert records to dictionary by date
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
            print(f"Error processing DTR data: {e}")
    
    return render_template(
        "admin/reports.html",
        employees=employees,
        employee_id=employee_id,
        month_year=month_year,
        dtr_data=dtr_data,
        employee_info=employee_info
    )


# ================= SETTINGS =================
@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    """Settings page for holidays and suspensions"""
    db = get_db()
    cur = db.cursor()
    
    if request.method == "POST":
        try:
            action = request.form.get("action")
            
            if action == "mark_holiday":
                holiday_date = request.form.get("holiday_date", "").strip()
                reason = request.form.get("reason", "Holiday").strip() or "Holiday"
                
                if not holiday_date:
                    return render_template("admin/settings.html", 
                                         error="Please select a date",
                                         success=None)
                
                # Get all active employees
                cur.execute("SELECT id FROM employees WHERE status='Active'")
                employees = cur.fetchall()
                
                if not employees:
                    return render_template("admin/settings.html",
                                         error="No active employees found",
                                         success=None)
                
                # Mark all employees as present for the holiday
                from datetime import datetime
                marked_count = 0
                
                for emp in employees:
                    employee_id = emp["id"]
                    
                    # Check if attendance record already exists
                    cur.execute("""
                        SELECT attendance_id FROM attendance 
                        WHERE employee_id=? AND date=?
                    """, (employee_id, holiday_date))
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
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
                        # Create new record
                        cur.execute("""
                            INSERT INTO attendance 
                            (employee_id, date, morning_in, lunch_out, afternoon_in, 
                             time_out, attendance_status, verification_method)
                            VALUES (?, ?, '08:00 AM', '12:00 PM', '01:00 PM', 
                                    '05:00 PM', 'Present', ?)
                        """, (employee_id, holiday_date, f"Admin: {reason}"))
                    
                    marked_count += 1
                
                db.commit()
                
                return render_template("admin/settings.html",
                                     success=f"Successfully marked {marked_count} employees as present for {holiday_date} ({reason})",
                                     error=None)
            
            elif action == "mark_suspension":
                suspension_date = request.form.get("suspension_date", "").strip()
                reason = request.form.get("reason", "Suspension").strip() or "Suspension"
                
                if not suspension_date:
                    return render_template("admin/settings.html",
                                         error="Please select a date",
                                         success=None)
                
                # Get all active employees
                cur.execute("SELECT id FROM employees WHERE status='Active'")
                employees = cur.fetchall()
                
                if not employees:
                    return render_template("admin/settings.html",
                                         error="No active employees found",
                                         success=None)
                
                # Mark all employees as present for the suspension
                marked_count = 0
                
                for emp in employees:
                    employee_id = emp["id"]
                    
                    # Check if attendance record already exists
                    cur.execute("""
                        SELECT attendance_id FROM attendance 
                        WHERE employee_id=? AND date=?
                    """, (employee_id, suspension_date))
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
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
                        # Create new record
                        cur.execute("""
                            INSERT INTO attendance 
                            (employee_id, date, morning_in, lunch_out, afternoon_in, 
                             time_out, attendance_status, verification_method)
                            VALUES (?, ?, '08:00 AM', '12:00 PM', '01:00 PM', 
                                    '05:00 PM', 'Present', ?)
                        """, (employee_id, suspension_date, f"Admin: {reason}"))
                    
                    marked_count += 1
                
                db.commit()
                
                return render_template("admin/settings.html",
                                     success=f"Successfully marked {marked_count} employees as present for {suspension_date} ({reason})",
                                     error=None)
        
        except Exception as e:
            db.rollback()
            print(f"Error in settings: {e}")
            import traceback
            traceback.print_exc()
            return render_template("admin/settings.html",
                                 error=f"Error: {str(e)}",
                                 success=None)
    
    # GET request - show settings page
    return render_template("admin/settings.html", error=None, success=None)


# ================= EMPLOYEE ATTENDANCE PAGE =================
@app.route("/attendance")
def employee_attendance():
    """Main page for employees to scan their face for attendance"""
    return render_template("employee_attendance.html")


# ================= HELPER FUNCTIONS =================
def check_if_late(time_str, time_type="morning"):
    """
    Check if a time string is late based on the time windows.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM" (e.g., "08:30 AM")
        time_type: "morning" or "afternoon"
    
    Returns:
        bool: True if late, False if on-time
    """
    try:
        from datetime import datetime
        
        # Parse the time string
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        
        if time_type == "morning":
            # Morning: late if >= 8:30 AM
            late_threshold = datetime.strptime("08:30 AM", "%I:%M %p")
            return time_obj >= late_threshold
        elif time_type == "afternoon":
            # Afternoon: late if >= 1:30 PM
            late_threshold = datetime.strptime("01:30 PM", "%I:%M %p")
            return time_obj >= late_threshold
        
        return False
    except Exception as e:
        print(f"Error checking late status: {e}")
        return False


def is_time_in_valid_window(time_str, time_type="morning"):
    """
    Check if time is within the valid time-in window.
    
    Args:
        time_str: Time string in format "HH:MM AM/PM"
        time_type: "morning" or "afternoon"
    
    Returns:
        bool: True if within window, False otherwise
    """
    try:
        from datetime import datetime
        
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        
        if time_type == "morning":
            # Morning window: 8:00 AM to 12:00 PM
            start_time = datetime.strptime("08:00 AM", "%I:%M %p")
            end_time = datetime.strptime("12:00 PM", "%I:%M %p")
            return start_time <= time_obj <= end_time
        elif time_type == "afternoon":
            # Afternoon window: 1:00 PM to 5:00 PM
            start_time = datetime.strptime("01:00 PM", "%I:%M %p")
            end_time = datetime.strptime("05:00 PM", "%I:%M %p")
            return start_time <= time_obj <= end_time
        
        return False
    except Exception as e:
        print(f"Error checking time window: {e}")
        return False


# ================= FACE RECOGNITION API =================
@app.route("/api/recognize-face", methods=["POST"])
def recognize_face():
    """API endpoint for face recognition and time-in"""
    try:
        data = request.get_json()
        image_data = data.get("image")
        
        if not image_data:
            return jsonify({"success": False, "message": "No image provided"}), 400
        
        # Encode face from base64 image
        face_encoding = face_utils.encode_face_from_base64(image_data)
        
        if face_encoding is None:
            return jsonify({"success": False, "message": "No face detected. Please position your face in the frame."})
        
        # Load known faces
        employee_ids, known_encodings = face_utils.load_known_faces()
        
        if not known_encodings:
            return jsonify({"success": False, "message": "No registered employees found."})
        
        # Compare with known faces
        import face_recognition
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        
        # Find best match
        best_match_index = None
        if True in matches:
            best_match_index = matches.index(True)
            # Use the closest match if multiple matches
            if len([m for m in matches if m]) > 1:
                best_match_index = min(range(len(matches)), key=lambda i: face_distances[i] if matches[i] else float('inf'))
        elif len(face_distances) > 0:
            # If no exact match, try with lower tolerance
            best_match_index = min(range(len(face_distances)), key=lambda i: face_distances[i])
            if face_distances[best_match_index] > 0.6:
                return jsonify({"success": False, "message": "Face not recognized. Please ensure you are registered."})
        
        if best_match_index is None:
            return jsonify({"success": False, "message": "Face not recognized. Please try again."})
        
        employee_id = employee_ids[best_match_index]
        
        # Get employee info
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        
        if not employee:
            return jsonify({"success": False, "message": "Employee not found."})
        
        # Check if employee is active
        if employee["status"] != "Active":
            return jsonify({"success": False, "message": "Your account is not active. Please contact administrator."})
        
        # Record attendance
        from datetime import datetime
        today = date.today().isoformat()
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Check existing attendance for today
        cur.execute("SELECT * FROM attendance WHERE employee_id=? AND date=?", (employee_id, today))
        existing = cur.fetchone()
        
        if existing:
            # Determine which time slot to update
            if not existing["morning_in"]:
                # Morning time in (8:00 AM to 12:00 PM)
                if not is_time_in_valid_window(current_time, "morning"):
                    return jsonify({
                        "success": False,
                        "message": f"Morning time-in window is 8:00 AM to 12:00 PM. Current time: {current_time}"
                    })
                
                # Check if late (>= 8:30 AM)
                is_late = check_if_late(current_time, "morning")
                attendance_status = "Late" if is_late else "Present"
                
                cur.execute("""
                    UPDATE attendance 
                    SET morning_in=?, attendance_status=?
                    WHERE employee_id=? AND date=?
                """, (current_time, attendance_status, employee_id, today))
                
                late_msg = " (Late)" if is_late else ""
                message = f"Good morning! Time in recorded at {current_time}{late_msg}"
                
            elif not existing["lunch_out"] and existing["morning_in"]:
                # Lunch out (should be around 12:00 PM)
                # Allow lunch out between 11:30 AM and 1:00 PM for flexibility
                time_obj = datetime.strptime(current_time, "%I:%M %p")
                lunch_start = datetime.strptime("11:30 AM", "%I:%M %p")
                lunch_end = datetime.strptime("01:00 PM", "%I:%M %p")
                
                if lunch_start <= time_obj <= lunch_end:
                    cur.execute("""
                        UPDATE attendance 
                        SET lunch_out=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, employee_id, today))
                    message = f"Lunch break recorded at {current_time}"
                else:
                    return jsonify({
                        "success": False,
                        "message": f"Lunch break time should be between 11:30 AM and 1:00 PM. Current time: {current_time}"
                    })
                    
            elif not existing["afternoon_in"] and existing["lunch_out"]:
                # Afternoon time in (1:00 PM to 5:00 PM)
                if not is_time_in_valid_window(current_time, "afternoon"):
                    return jsonify({
                        "success": False,
                        "message": f"Afternoon time-in window is 1:00 PM to 5:00 PM. Current time: {current_time}"
                    })
                
                # Check if late (>= 1:30 PM)
                is_late_afternoon = check_if_late(current_time, "afternoon")
                
                # Check if morning was late by checking morning_in time
                morning_was_late = False
                if existing["morning_in"]:
                    morning_was_late = check_if_late(existing["morning_in"], "morning")
                
                # Update status: if afternoon is late OR morning was late, mark as Late
                if is_late_afternoon or morning_was_late:
                    attendance_status = "Late"
                else:
                    attendance_status = "Present"
                
                cur.execute("""
                    UPDATE attendance 
                    SET afternoon_in=?, attendance_status=?
                    WHERE employee_id=? AND date=?
                """, (current_time, attendance_status, employee_id, today))
                
                late_msg = " (Late)" if is_late_afternoon else ""
                message = f"Afternoon time in recorded at {current_time}{late_msg}"
                
            elif not existing["time_out"]:
                # Time out (should be around 5:00 PM)
                # Allow time out between 4:30 PM and 7:00 PM for flexibility
                time_obj = datetime.strptime(current_time, "%I:%M %p")
                out_start = datetime.strptime("04:30 PM", "%I:%M %p")
                out_end = datetime.strptime("07:00 PM", "%I:%M %p")
                
                if out_start <= time_obj <= out_end:
                    cur.execute("""
                        UPDATE attendance 
                        SET time_out=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, employee_id, today))
                    message = f"Time out recorded at {current_time}. Have a great day!"
                else:
                    return jsonify({
                        "success": False,
                        "message": f"Time out should be between 4:30 PM and 7:00 PM. Current time: {current_time}"
                    })
            else:
                message = f"All attendance records for today are complete. Last update: {current_time}"
        else:
            # Create new attendance record (morning time in)
            # Check if within morning window (8:00 AM to 12:00 PM)
            if not is_time_in_valid_window(current_time, "morning"):
                return jsonify({
                    "success": False,
                    "message": f"Morning time-in window is 8:00 AM to 12:00 PM. Current time: {current_time}"
                })
            
            # Check if late (>= 8:30 AM)
            is_late = check_if_late(current_time, "morning")
            attendance_status = "Late" if is_late else "Present"
            
            cur.execute("""
                INSERT INTO attendance (employee_id, date, morning_in, attendance_status, verification_method)
                VALUES (?, ?, ?, ?, 'Face Recognition')
            """, (employee_id, today, current_time, attendance_status))
            
            late_msg = " (Late)" if is_late else ""
            message = f"Good morning! Time in recorded at {current_time}{late_msg}"
        
        db.commit()
        
        return jsonify({
            "success": True,
            "employee": {
                "id": employee["id"],
                "full_name": employee["full_name"],
                "employee_code": employee["employee_code"]
            },
            "time_in": current_time,
            "message": message
        })
        
    except Exception as e:
        print(f"Error in face recognition: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error processing face recognition: {str(e)}"}), 500


# ================= ATTENDANCE HISTORY API =================
@app.route("/api/attendance-history")
def attendance_history():
    """API endpoint to get attendance history for the current employee"""
    try:
        # For now, return all attendance records (in production, filter by logged-in employee)
        # You can modify this to use session or employee_id parameter
        filter_type = request.args.get("filter", "week")
        
        db = get_db()
        cur = db.cursor()
        
        from datetime import datetime, timedelta
        
        if filter_type == "week":
            start_date = (datetime.now() - timedelta(days=7)).date().isoformat()
        else:  # month
            start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        
        # Get all recent attendance records
        cur.execute("""
            SELECT e.full_name, a.date, a.morning_in, a.lunch_out, 
                   a.afternoon_in, a.time_out, a.attendance_status
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.date >= ?
            ORDER BY a.date DESC, e.full_name
            LIMIT 50
        """, (start_date,))
        
        records = cur.fetchall()
        
        # Format records
        formatted_records = []
        for record in records:
            date_obj = datetime.strptime(record["date"], "%Y-%m-%d")
            today = datetime.now().date()
            
            if date_obj.date() == today:
                date_label = f"Today, {date_obj.strftime('%b %d, %Y')} ({record['full_name']})"
            elif date_obj.date() == today - timedelta(days=1):
                date_label = f"Yesterday, {date_obj.strftime('%b %d, %Y')} ({record['full_name']})"
            else:
                date_label = f"{date_obj.strftime('%b %d, %Y')} ({record['full_name']})"
            
            formatted_records.append({
                "date_label": date_label,
                "date": record["date"],
                "morning_in": record["morning_in"],
                "lunch_out": record["lunch_out"],
                "afternoon_in": record["afternoon_in"],
                "time_out": record["time_out"],
                "status": record["attendance_status"]
            })
        
        return jsonify({
            "success": True,
            "records": formatted_records
        })
        
    except Exception as e:
        print(f"Error loading attendance history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "Error loading attendance history"}), 500


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)