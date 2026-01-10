"""
API blueprint for REST API endpoints
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import date, datetime, timedelta
from utils.logger import get_logger
import face_utils
import face_recognition

logger = get_logger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import session, redirect, url_for
        if not session.get("admin_logged_in"):
            logger.warning("Unauthorized API access attempt")
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return wrapper


@api_bp.route("/dashboard-stats")
@admin_required
def dashboard_stats():
    """API endpoint to get dashboard statistics for auto-refresh"""
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
        
        recent_list = []
        for record in recent_attendance:
            recent_list.append({
                "full_name": record["full_name"],
                "employee_code": record["employee_code"],
                "date": record["date"],
                "morning_in": record["morning_in"],
                "lunch_out": record["lunch_out"],
                "afternoon_in": record["afternoon_in"],
                "time_out": record["time_out"],
                "attendance_status": record["attendance_status"]
            })

        return jsonify({
            "success": True,
            "total_employees": total_employees,
            "present": present,
            "absent": absent,
            "late": late,
            "recent_attendance": recent_list
        })
    except Exception as e:
        logger.error(f"Error in dashboard_stats API: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Error loading dashboard statistics"}), 500


@api_bp.route("/attendance-records")
@admin_required
def attendance_records():
    """API endpoint to get attendance records for auto-refresh"""
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
        
        records_list = []
        for record in records:
            records_list.append({
                "attendance_id": record["attendance_id"],
                "full_name": record["full_name"],
                "date": record["date"],
                "morning_in": record["morning_in"],
                "lunch_out": record["lunch_out"],
                "afternoon_in": record["afternoon_in"],
                "time_out": record["time_out"],
                "attendance_status": record["attendance_status"]
            })
        
        return jsonify({
            "success": True,
            "selected_date": selected_date,
            "records": records_list
        })
    except Exception as e:
        logger.error(f"Error in attendance_records API: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Error loading attendance records"}), 500


@api_bp.route("/recognize-face", methods=["POST"])
def recognize_face():
    """API endpoint for face recognition and time-in"""
    try:
        data = request.get_json()
        image_data = data.get("image")
        
        if not image_data:
            logger.warning("Face recognition API called without image data")
            return jsonify({"success": False, "message": "No image provided"}), 400
        
        logger.info("Starting face recognition...")
        
        # Encode face from base64 image
        face_encoding = face_utils.encode_face_from_base64(image_data)
        
        if face_encoding is None:
            logger.warning("No face detected in image")
            return jsonify({"success": False, "message": "No face detected. Please ensure your face is clearly visible in the camera frame and well-lit."})
        
        logger.debug("Face encoding successful")
        
        # Load known faces
        employee_ids, known_encodings = face_utils.load_known_faces()
        
        if not known_encodings:
            logger.error("No registered employees found in database")
            return jsonify({"success": False, "message": "No registered employees found. Please contact administrator."})
        
        logger.debug(f"Loaded {len(known_encodings)} known face encodings")
        
        # Compare with known faces
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        
        best_match_index = None
        if len(face_distances) > 0:
            min_distance = min(face_distances)
            best_match_index = min(range(len(face_distances)), key=lambda i: face_distances[i])
            logger.debug(f"Minimum face distance: {min_distance:.4f} (threshold: 0.6)")
            
            # Try with standard tolerance first (0.6)
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
            
            # If no match with standard tolerance, try with more lenient tolerance (0.65)
            if not any(matches) and min_distance <= 0.65:
                logger.debug("No match with tolerance 0.6, trying 0.65...")
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.65)
            
            # If still no match, try even more lenient (0.7)
            if not any(matches) and min_distance <= 0.7:
                logger.debug("No match with tolerance 0.65, trying 0.7...")
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.7)
            
            logger.debug(f"Face comparison results: {len([m for m in matches if m])} matches found")
            
            if any(matches):
                # Find the best matching index
                if len([m for m in matches if m]) > 1:
                    best_match_index = min(range(len(matches)), key=lambda i: face_distances[i] if matches[i] else float('inf'))
                else:
                    best_match_index = matches.index(True)
                logger.info(f"Face match found at index {best_match_index}, employee_id: {employee_ids[best_match_index]}")
            elif min_distance > 0.7:
                similarity = (1 - min_distance) * 100
                logger.warning(f"Face not recognized - distance too high: {min_distance:.4f}, similarity: {similarity:.1f}%")
                return jsonify({
                    "success": False, 
                    "message": f"Face not recognized. Your face doesn't match any registered employee. Please ensure you are registered in the system. (Similarity: {similarity:.1f}%)"
                })
            else:
                logger.warning(f"Acceptable distance ({min_distance:.4f}) but no match found")
        else:
            logger.error("No face distances calculated")
            return jsonify({"success": False, "message": "Error processing face recognition. Please try again."})
        
        if best_match_index is None:
            logger.warning("No match found in face recognition")
            return jsonify({"success": False, "message": "Face not recognized. Please ensure you are registered in the system."})
        
        employee_id = employee_ids[best_match_index]
        
        # Get employee info
        from db import get_db
        from utils.helpers import check_if_late, is_morning_time_in_allowed
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        employee = cur.fetchone()
        
        if not employee:
            logger.error(f"Employee not found for ID: {employee_id}")
            return jsonify({"success": False, "message": "Employee not found."})
        
        # Check if employee is active
        # sqlite3.Row objects use bracket notation, not .get()
        # Handle case where status column might not exist (for older databases)
        try:
            employee_status = employee["status"] if "status" in employee.keys() else "Active"
        except (KeyError, TypeError):
            employee_status = "Active"  # Default to Active if status column doesn't exist
        
        if employee_status and employee_status != "Active":
            logger.warning(f"Inactive employee attempted attendance: {employee_id}, status: {employee_status}")
            return jsonify({"success": False, "message": "Your account is not active. Please contact administrator."})
        
        # Record attendance
        today = date.today().isoformat()
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Check existing attendance for today
        cur.execute("SELECT * FROM attendance WHERE employee_id=? AND date=?", (employee_id, today))
        existing = cur.fetchone()
        
        message = ""
        if existing:
            # Parse current time to determine which slot to fill
            time_obj = datetime.strptime(current_time, "%I:%M %p")
            afternoon_start = datetime.strptime("12:00 PM", "%I:%M %p")
            
            if time_obj >= afternoon_start:
                # Afternoon time
                if not existing["afternoon_in"]:
                    is_late_afternoon = check_if_late(current_time, "afternoon")
                    morning_was_late = False
                    if existing["morning_in"]:
                        morning_was_late = check_if_late(existing["morning_in"], "morning")
                    
                    attendance_status = "Late" if (is_late_afternoon or morning_was_late) else "Present"
                    
                    cur.execute("""
                        UPDATE attendance 
                        SET afternoon_in=?, attendance_status=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, attendance_status, employee_id, today))
                    
                    late_msg = " (Late)" if is_late_afternoon else ""
                    message = f"Afternoon time in recorded at {current_time}{late_msg}"
                elif not existing["time_out"]:
                    cur.execute("""
                        UPDATE attendance 
                        SET time_out=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, employee_id, today))
                    message = f"Time out recorded at {current_time}. Have a great day!"
                else:
                    message = f"All attendance records for today are complete. Last update: {current_time}"
            else:
                # Morning time
                if not existing["morning_in"]:
                    if not is_morning_time_in_allowed(current_time):
                        return jsonify({
                            "success": False,
                            "message": f"Morning time-in is allowed from 5:00 AM onwards. Current time: {current_time}"
                        })
                    
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
                    # Employees can time out for lunch at any time (no restriction)
                    cur.execute("""
                        UPDATE attendance 
                        SET lunch_out=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, employee_id, today))
                    message = f"Lunch break recorded at {current_time}"
                elif not existing["afternoon_in"]:
                    is_late_afternoon = check_if_late(current_time, "afternoon")
                    morning_was_late = False
                    if existing["morning_in"]:
                        morning_was_late = check_if_late(existing["morning_in"], "morning")
                    
                    attendance_status = "Late" if (is_late_afternoon or morning_was_late) else "Present"
                    
                    cur.execute("""
                        UPDATE attendance 
                        SET afternoon_in=?, attendance_status=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, attendance_status, employee_id, today))
                    
                    late_msg = " (Late)" if is_late_afternoon else ""
                    message = f"Afternoon time in recorded at {current_time}{late_msg}"
                elif not existing["time_out"]:
                    cur.execute("""
                        UPDATE attendance 
                        SET time_out=?
                        WHERE employee_id=? AND date=?
                    """, (current_time, employee_id, today))
                    message = f"Time out recorded at {current_time}. Have a great day!"
                else:
                    message = f"All attendance records for today are complete. Last update: {current_time}"
        else:
            # Create new attendance record
            time_obj = datetime.strptime(current_time, "%I:%M %p")
            afternoon_start = datetime.strptime("12:00 PM", "%I:%M %p")
            
            if time_obj >= afternoon_start:
                # Afternoon time
                is_late = check_if_late(current_time, "afternoon")
                attendance_status = "Late" if is_late else "Present"
                
                cur.execute("""
                    INSERT INTO attendance (employee_id, date, afternoon_in, attendance_status, verification_method)
                    VALUES (?, ?, ?, ?, 'Face Recognition')
                """, (employee_id, today, current_time, attendance_status))
                
                late_msg = " (Late)" if is_late else ""
                message = f"Afternoon time in recorded at {current_time}{late_msg}"
            else:
                # Morning time
                if not is_morning_time_in_allowed(current_time):
                    return jsonify({
                        "success": False,
                        "message": f"Morning time-in is allowed from 5:00 AM onwards. Current time: {current_time}"
                    })
                
                is_late = check_if_late(current_time, "morning")
                attendance_status = "Late" if is_late else "Present"
                
                cur.execute("""
                    INSERT INTO attendance (employee_id, date, morning_in, attendance_status, verification_method)
                    VALUES (?, ?, ?, ?, 'Face Recognition')
                """, (employee_id, today, current_time, attendance_status))
                
                late_msg = " (Late)" if is_late else ""
                message = f"Good morning! Time in recorded at {current_time}{late_msg}"
        
        db.commit()
        logger.info(f"Attendance recorded for employee {employee_id} at {current_time}")
        
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
        logger.error(f"Error in face recognition: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Error processing face recognition: {str(e)}"}), 500


@api_bp.route("/attendance-history")
def attendance_history():
    """API endpoint to get attendance history for the current employee"""
    try:
        from db import get_db
        db = get_db()
        cur = db.cursor()
        
        filter_type = request.args.get("filter", "week")
        
        if filter_type == "week":
            start_date = (datetime.now() - timedelta(days=7)).date().isoformat()
        else:  # month
            start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        
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
        logger.error(f"Error loading attendance history: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Error loading attendance history"}), 500
