import cv2
import face_recognition
import time
from datetime import datetime, date
from database import get_db
from face_utils import decode_from_blob

# ================= PERFORMANCE SETTINGS =================
FRAME_SCALE = 0.20          # Smaller = faster
RECOGNITION_INTERVAL = 2   # seconds (KEY to smoothness)
MATCH_THRESHOLD = 0.55
MAX_FPS = 15               # CCTV-like smoothness
SCAN_COOLDOWN = 10         # seconds per employee

# ================= GLOBAL STATE =================
camera = None
camera_running = False
current_action = None

KNOWN_FACES = []
last_recognition = 0
last_scan = {}

cached_boxes = []
cached_names = []

# ================= LOAD FACES =================
def load_faces():
    db = get_db()
    rows = db.execute("""
        SELECT employee.employee_id, employee.full_name, facial_data.face_encoding
        FROM facial_data
        JOIN employee ON employee.employee_id = facial_data.employee_id
    """).fetchall()
    db.close()

    faces = []
    for r in rows:
        faces.append({
            "id": r["employee_id"],
            "name": r["full_name"],
            "encoding": decode_from_blob(r["face_encoding"])
        })

    print(f"[INFO] Loaded {len(faces)} known faces")
    return faces

# ================= CAMERA CONTROL =================
def set_action(action):
    global camera_running, camera, current_action, KNOWN_FACES

    current_action = action

    if not camera_running:
        KNOWN_FACES = load_faces()
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, MAX_FPS)
        camera_running = True

def stop_camera():
    global camera_running, camera, current_action
    current_action = None
    if camera:
        camera.release()
    camera_running = False

# ================= SAVE ATTENDANCE =================
def save_attendance(emp_id):
    db = get_db()
    today = date.today().isoformat()
    time_now = datetime.now().strftime("%I:%M:%S %p")

    rec = db.execute("""
        SELECT * FROM attendance
        WHERE employee_id=? AND date=?
    """, (emp_id, today)).fetchone()

    if rec is None:
        db.execute("""
            INSERT INTO attendance (employee_id, date, morning_in)
            VALUES (?, ?, ?)
        """, (emp_id, today, time_now))
    else:
        if current_action and rec[current_action] is None:
            db.execute(f"""
                UPDATE attendance SET {current_action}=?
                WHERE attendance_id=?
            """, (time_now, rec["attendance_id"]))

    db.commit()
    db.close()

# ================= VIDEO STREAM =================
def gen_frames():
    global last_recognition, cached_boxes, cached_names

    while camera_running:
        frame_start = time.time()

        success, frame = camera.read()
        if not success:
            break

        display = frame.copy()
        now = time.time()

        # ===== RUN FACE RECOGNITION ONLY EVERY X SECONDS =====
        if now - last_recognition > RECOGNITION_INTERVAL:
            last_recognition = now
            cached_boxes.clear()
            cached_names.clear()

            small = cv2.resize(
                frame, (0, 0),
                fx=FRAME_SCALE, fy=FRAME_SCALE
            )
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, locations)

            for enc, loc in zip(encodings, locations):
                top, right, bottom, left = [
                    int(v / FRAME_SCALE) for v in loc
                ]

                name = "Unknown"

                for face in KNOWN_FACES:
                    dist = face_recognition.face_distance(
                        [face["encoding"]], enc
                    )[0]

                    if dist < MATCH_THRESHOLD:
                        name = face["name"]
                        emp_id = face["id"]

                        if emp_id not in last_scan or now - last_scan[emp_id] > SCAN_COOLDOWN:
                            last_scan[emp_id] = now
                            save_attendance(emp_id)
                            stop_camera()
                        break

                cached_boxes.append((left, top, right, bottom))
                cached_names.append(name)

        # ===== DRAW CACHED BOXES (FAST, NO LAG) =====
        for (l, t, r, b), name in zip(cached_boxes, cached_names):
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(display, (l, t), (r, b), color, 2)
            cv2.putText(
                display, name,
                (l, t - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, color, 2
            )

        # ===== STREAM FRAME =====
        ret, buffer = cv2.imencode(".jpg", display)
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )

        # ===== FPS LIMITER =====
        elapsed = time.time() - frame_start
        sleep_time = max(0, (1 / MAX_FPS) - elapsed)
        time.sleep(sleep_time)
