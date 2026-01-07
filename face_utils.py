import face_recognition
import numpy as np
import sqlite3
import cv2
import base64
from io import BytesIO
from PIL import Image

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

def encode_face_from_base64(base64_string):
    """Encode face from base64 image string"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64 to image
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        
        # Convert PIL image to numpy array (PIL images are already RGB)
        image_array = np.array(image)
        
        # Ensure image is RGB format (face_recognition expects RGB)
        if len(image_array.shape) == 3 and image_array.shape[2] == 4:
            # Convert RGBA to RGB
            rgb_image = image_array[:, :, :3]
        elif len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # Already RGB
            rgb_image = image_array
        elif len(image_array.shape) == 2:
            # Grayscale, convert to RGB
            rgb_image = np.stack([image_array] * 3, axis=2)
        else:
            rgb_image = image_array
        
        # Find face locations
        locations = face_recognition.face_locations(rgb_image)
        if not locations:
            return None
        
        # Get face encodings
        encodings = face_recognition.face_encodings(rgb_image, locations)
        if not encodings:
            return None
        
        return encodings[0]
    except Exception as e:
        print(f"Error encoding face from base64: {e}")
        return None

def save_face(employee_id, encoding):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO facial_data (employee_id, face_encoding) VALUES (?, ?)",
        (employee_id, encoding.tobytes())
    )
    db.commit()
    db.close()

def load_known_faces():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT employee_id, face_encoding FROM facial_data")
    rows = cursor.fetchall()
    db.close()

    ids = []
    encodings = []

    for r in rows:
        ids.append(r[0])
        encodings.append(np.frombuffer(r[1], dtype=np.float64))

    return ids, encodings
