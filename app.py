from flask import (
    Flask, render_template, Response,
    redirect, url_for, session, flash, request
)
from datetime import datetime
import cv2

from database import get_db
from camera import gen_frames, set_action, stop_camera
from face_utils import get_face_encoding, encode_to_blob

app = Flask(__name__)
app.secret_key = "biometric-secret-key"

# ================= HOME =================
@app.route("/")
def index():
    return redirect(url_for("camera_page"))

# ================= EMPLOYEE =================
@app.route("/camera")
def camera_page():
    return render_template("camera.html")

@app.route("/start/<action>", methods=["POST"])
def start_action(action):
    hour = datetime.now().hour

    rules = {
        "morning_in": (6, 12),
        "lunch_out": (12, 13),
        "afternoon_in": (13, 17),
        "time_out": (17, 24)
    }

    if action not in rules:
        flash("Invalid action")
        return redirect(url_for("camera_page"))

    start, end = rules[action]

    if not (start <= hour < end):
        flash("❌ This action is not allowed at this time.")
        stop_camera()
        return redirect(url_for("camera_page"))

    session["attendance_action"] = action
    set_action(action)
    return redirect(url_for("camera_page"))

@app.route("/video_feed")
def video_feed():
    if "attendance_action" not in session:
        return "", 204
    return Response(
        gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/stop")
def stop():
    session.pop("attendance_action", None)
    stop_camera()
    return redirect(url_for("camera_page"))

# ================= ADMIN =================
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid login")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    db = get_db()
    employees = db.execute("SELECT * FROM employee").fetchall()
    db.close()

    return render_template("admin_dashboard.html", employees=employees)

@app.route("/admin/add_employee", methods=["POST"])
def add_employee():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    db = get_db()
    db.execute(
        "INSERT INTO employee (full_name, id_number) VALUES (?, ?)",
        (request.form["full_name"], request.form["id_number"])
    )
    db.commit()
    db.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/enroll/<int:employee_id>")
def enroll_page(employee_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("upload_face.html", employee_id=employee_id)

@app.route("/admin/enroll_face", methods=["POST"])
def enroll_face():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    employee_id = request.form["employee_id"]

    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    encoding = get_face_encoding(frame)
    if encoding is None:
        flash("No face detected")
        return redirect(url_for("admin_dashboard"))

    blob = encode_to_blob(encoding)

    db = get_db()
    existing = db.execute(
        "SELECT * FROM facial_data WHERE employee_id=?",
        (employee_id,)
    ).fetchone()

    if existing:
        db.execute(
            "UPDATE facial_data SET face_encoding=? WHERE employee_id=?",
            (blob, employee_id)
        )
    else:
        db.execute(
            "INSERT INTO facial_data (employee_id, face_encoding) VALUES (?, ?)",
            (employee_id, blob)
        )

    db.commit()
    db.close()

    return redirect(url_for("admin_dashboard"))

# ================= ADMIN ATTENDANCE =================
@app.route("/admin/attendance")
def admin_attendance():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    db = get_db()
    records = db.execute("""
        SELECT employee.full_name,
               attendance.date,
               attendance.morning_in,
               attendance.lunch_out,
               attendance.afternoon_in,
               attendance.time_out
        FROM attendance
        JOIN employee ON employee.employee_id = attendance.employee_id
        ORDER BY attendance.date DESC
    """).fetchall()
    db.close()

    return render_template("admin_attendance.html", records=records)

# ================= DELETE EMPLOYEE (FIXED) =================
@app.route("/admin/delete_employee/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    print("DELETE ROUTE HIT:", employee_id)  # debug

    db = get_db()
    db.execute("DELETE FROM attendance WHERE employee_id=?", (employee_id,))
    db.execute("DELETE FROM facial_data WHERE employee_id=?", (employee_id,))
    db.execute("DELETE FROM employee WHERE employee_id=?", (employee_id,))
    db.commit()
    db.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# ================= RUN =================
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

