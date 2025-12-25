import face_recognition
import numpy as np
import sqlite3

DB = "biometric.db"

def get_db():
    return sqlite3.connect(DB)

def encode_face_from_frame(frame):
    rgb = frame[:, :, ::-1]
    locations = face_recognition.face_locations(rgb)
    if not locations:
        return None
    encodings = face_recognition.face_encodings(rgb, locations)
    return encodings[0]

def save_face(employee_id, encoding):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO facial_data (employee_id, face_encoding) VALUES (?, ?)",
        (employee_id, encoding.tobytes())
    )
    db.commit()
    db.close()

def load_known_faces():
    db = get_db()
    rows = db.execute("SELECT employee_id, face_encoding FROM facial_data").fetchall()
    db.close()

    ids = []
    encodings = []

    for r in rows:
        ids.append(r[0])
        encodings.append(np.frombuffer(r[1], dtype=np.float64))

    return ids, encodings
