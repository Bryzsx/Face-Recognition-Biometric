import face_recognition
import numpy as np
import sqlite3
import cv2
import base64
from io import BytesIO
from PIL import Image
from utils.logger import get_logger
from config import DATABASE

logger = get_logger(__name__)

def get_db():
    """Get database connection - use Flask's connection if available, otherwise standalone"""
    try:
        from flask import g, has_request_context
        # If we're in a Flask request context, use Flask's database connection
        if has_request_context() and "db" in g:
            return g.db
    except ImportError:
        pass
    except RuntimeError:
        # Not in a request context, use standalone connection
        pass
    
    # Use standalone connection with proper timeout
    return sqlite3.connect(DATABASE, timeout=30.0)

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
        
        # Try to find face locations with default model (hog - faster)
        locations = face_recognition.face_locations(rgb_image, model='hog')
        
        # If no face found with hog, try with cnn model (more accurate but slower)
        if not locations:
            logger.debug("No face found with 'hog' model, trying 'cnn' model...")
            locations = face_recognition.face_locations(rgb_image, model='cnn')
        
        if not locations:
            logger.warning("No face detected in image")
            return None
        
        logger.debug(f"Face detected at location: {locations[0]}")
        
        # Get face encodings
        encodings = face_recognition.face_encodings(rgb_image, locations)
        if not encodings:
            logger.warning("Failed to generate face encoding")
            return None
        
        logger.debug("Face encoding generated successfully")
        return encodings[0]
    except Exception as e:
        logger.error(f"Error encoding face from base64: {str(e)}", exc_info=True)
        return None







def save_face(employee_id, encoding):
    """Save face encoding to database - ensure float32 format"""
    db = None
    try:
        from flask import has_request_context, g
        # Check if we're in a Flask request context
        in_request_context = False
        try:
            in_request_context = has_request_context() and "db" in g
        except RuntimeError:
            pass
        
        # Ensure encoding is float32 (face_recognition uses float32)
        if encoding.dtype != np.float32:
            encoding = encoding.astype(np.float32)
        
        # Verify encoding shape (should be 128 for face_recognition)
        if encoding.shape[0] != 128:
            logger.error(f"Invalid encoding shape: {encoding.shape}, expected 128. Cannot save for employee {employee_id}")
            return False
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO facial_data (employee_id, face_encoding) VALUES (?, ?)",
            (employee_id, encoding.tobytes())
        )
        
        # Only commit and close if we created a standalone connection
        if not in_request_context:
            db.commit()
            db.close()
            db = None
        else:
            # If using Flask's connection, let Flask handle commit/close
            db.commit()
        
        logger.info(f"Face encoding saved for employee {employee_id}, dtype: {encoding.dtype}, shape: {encoding.shape}, size: {encoding.nbytes} bytes")
        return True
    except Exception as e:
        logger.error(f"Error saving face encoding for employee {employee_id}: {str(e)}", exc_info=True)
        return False
    finally:
        # Ensure standalone connection is closed
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

def load_known_faces():
    """Load all known face encodings from the database"""
    db = None
    try:
        from flask import has_request_context, g
        # Check if we're in a Flask request context
        in_request_context = False
        try:
            in_request_context = has_request_context() and "db" in g
        except RuntimeError:
            pass
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT employee_id, face_encoding FROM facial_data")
        rows = cursor.fetchall()
        
        # Only close if we created a standalone connection (not Flask's)
        if not in_request_context:
            db.close()
            db = None

        ids = []
        encodings = []

        for r in rows:
            try:
                employee_id = r[0]
                face_encoding_bytes = r[1]
                
                if not face_encoding_bytes:
                    logger.warning(f"Empty face encoding for employee_id {employee_id}")
                    continue
                
                # Try to determine the correct dtype based on size
                # face_recognition uses float32 (128 elements = 512 bytes)
                # But old encodings might be float64 (128 elements = 1024 bytes)
                encoding_size = len(face_encoding_bytes)
                
                # Try float32 first (correct format - 512 bytes)
                if encoding_size == 512:
                    encoding = np.frombuffer(face_encoding_bytes, dtype=np.float32)
                # Try float64 (old format - 1024 bytes)
                elif encoding_size == 1024:
                    logger.warning(f"Converting float64 encoding to float32 for employee_id {employee_id}")
                    encoding_float64 = np.frombuffer(face_encoding_bytes, dtype=np.float64)
                    # Convert to float32 (face_recognition expects float32)
                    encoding = encoding_float64.astype(np.float32)
                else:
                    logger.warning(f"Unexpected encoding size {encoding_size} bytes for employee_id {employee_id}. Expected 512 (float32) or 1024 (float64)")
                    # Try to guess - if divisible by 8, might be float64
                    if encoding_size % 8 == 0 and encoding_size // 8 == 128:
                        encoding_float64 = np.frombuffer(face_encoding_bytes, dtype=np.float64)
                        encoding = encoding_float64.astype(np.float32)
                    elif encoding_size % 4 == 0 and encoding_size // 4 == 128:
                        encoding = np.frombuffer(face_encoding_bytes, dtype=np.float32)
                    else:
                        logger.error(f"Cannot determine encoding format for employee_id {employee_id}. Size: {encoding_size} bytes")
                        continue
                
                # Verify encoding shape (should be 128 for face_recognition)
                if encoding.shape[0] != 128:
                    logger.warning(f"Invalid encoding shape for employee_id {employee_id}: {encoding.shape}, expected 128. Skipping.")
                    continue
                
                # Ensure it's float32
                if encoding.dtype != np.float32:
                    encoding = encoding.astype(np.float32)
                
                ids.append(employee_id)
                encodings.append(encoding)
                logger.debug(f"Loaded encoding for employee_id: {employee_id}, dtype: {encoding.dtype}, shape: {encoding.shape}, size: {encoding.nbytes} bytes")
            except Exception as e:
                logger.warning(f"Error loading encoding for employee_id {r[0]}: {str(e)}", exc_info=True)
                continue

        logger.info(f"Successfully loaded {len(encodings)} face encodings")
        return ids, encodings
    except Exception as e:
        logger.error(f"Error in load_known_faces: {str(e)}", exc_info=True)
        return [], []
    finally:
        # Ensure standalone connection is closed
        if db is not None:
            try:
                db.close()
            except Exception:
                pass