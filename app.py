from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from functools import wraps
from datetime import date

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

    return render_template(
        "admin/dashboard.html",
        total_employees=total_employees,
        present=present,
        absent=absent,
        late=late,
    )


# ================= REGISTER =================
@app.route("/admin/register", methods=["GET", "POST"])
@admin_required
def admin_register():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("""
            INSERT INTO employees (full_name, employee_code, department, position)
            VALUES (?, ?, ?, ?)
        """, (
            request.form["full_name"],
            request.form["employee_id"],
            request.form["department"],
            request.form["position"],
        ))

        db.commit()
        return redirect(url_for("admin_employees"))

    return render_template("admin/register.html")


# ================= EMPLOYEES =================
@app.route("/admin/employees")
@admin_required
def admin_employees():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()
    return render_template("admin/employees.html", employees=employees)


# ================= EMPLOYEE INFO =================
@app.route("/admin/employee-info")
@admin_required
def admin_employee_info():
    return render_template("admin/employee_info.html")


# ================= ATTENDANCE =================
@app.route("/admin/attendance")
@admin_required
def admin_attendance():
    db = get_db()
    cur = db.cursor()
    today = date.today().isoformat()

    cur.execute("""
        SELECT e.full_name, a.date, a.morning_in, a.attendance_status
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date=?
    """, (today,))

    records = cur.fetchall()
    return render_template("admin/attendance.html", records=records)


# ================= REPORTS =================
@app.route("/admin/reports")
@admin_required
def admin_reports():
    return render_template("admin/reports.html")


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)