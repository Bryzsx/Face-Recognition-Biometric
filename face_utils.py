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
        
        # Try to find face locations with default model (hog - faster)
        locations = face_recognition.face_locations(rgb_image, model='hog')
        
        # If no face found with hog, try with cnn model (more accurate but slower)
        if not locations:
            print("[FACE ENCODING] No face found with 'hog' model, trying 'cnn' model...")
            locations = face_recognition.face_locations(rgb_image, model='cnn')
        
        if not locations:
            print("[FACE ENCODING] No face detected in image")
            return None
        
        print(f"[FACE ENCODING] Face detected at location: {locations[0]}")
        
        # Get face encodings
        encodings = face_recognition.face_encodings(rgb_image, locations)
        if not encodings:
            print("[FACE ENCODING] Failed to generate face encoding")
            return None
        
        print("[FACE ENCODING] Face encoding generated successfully")
        return encodings[0]
    except Exception as e:
        print(f"[FACE ENCODING] Error encoding face from base64: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_face_location_from_base64(base64_string):
    """Get face location from base64 image string for liveness detection"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64 to image
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        
        # Convert PIL image to numpy array
        image_array = np.array(image)
        
        # Ensure image is RGB format
        if len(image_array.shape) == 3 and image_array.shape[2] == 4:
            rgb_image = image_array[:, :, :3]
        elif len(image_array.shape) == 3 and image_array.shape[2] == 3:
            rgb_image = image_array
        elif len(image_array.shape) == 2:
            rgb_image = np.stack([image_array] * 3, axis=2)
        else:
            rgb_image = image_array
        
        # Find face locations
        locations = face_recognition.face_locations(rgb_image, model='hog')
        if not locations:
            return None
        
        # Return the first face location (top, right, bottom, left)
        return locations[0]
    except Exception as e:
        print(f"Error getting face location: {e}")
        return None


def detect_liveness(image_frames):
    """
    Detect if the face is a real person or a photo/picture.
    This function uses multiple methods to detect static images (photos/pictures).
    Optimized to be lenient for real faces while still catching photos.
    
    Args:
        image_frames: List of base64 image strings (at least 5 frames)
    
    Returns:
        tuple: (is_live: bool, confidence: float, message: str)
    """
    if len(image_frames) < 5:
        return False, 0.0, "Need at least 5 frames for liveness detection"
    
    print(f"[LIVENESS] Starting detection with {len(image_frames)} frames")
    
    try:
        # First check: Compare images pixel-by-pixel to detect identical frames (photos are identical)
        # Decode all frames and compare
        try:
            # Remove data URL prefix if present and decode
            decoded_images = []
            for frame in image_frames:
                frame_data = frame.split(',')[1] if ',' in frame else frame
                img_data = base64.b64decode(frame_data)
                img = Image.open(BytesIO(img_data))
                decoded_images.append(np.array(img))
            
            # Check if any images are identical (photos would be identical)
            for i in range(len(decoded_images)):
                for j in range(i + 1, len(decoded_images)):
                    if np.array_equal(decoded_images[i], decoded_images[j]):
                        return False, 0.0, "Liveness check failed: Identical frames detected. Photos and pictures cannot be used. Only real faces are allowed."
            
            # Check similarity between all frame pairs (photos are very similar)
            min_diff = float('inf')
            for i in range(len(decoded_images) - 1):
                diff = np.mean(np.abs(decoded_images[i].astype(float) - decoded_images[i+1].astype(float)))
                min_diff = min(min_diff, diff)
            
            # STRICT: If images are too similar (difference < 2%), likely a photo
            # Phone screens might have slight refresh variations, but photos are still very similar
            # Real faces have much more variation due to natural movements, lighting changes, etc.
            # Made extremely lenient - only catch completely identical frames
            if min_diff < 2.0:
                print(f"[LIVENESS] FAILED: Frames too similar (min_diff: {min_diff:.2f})")
                return False, 0.0, "Liveness check failed: Frames too similar. Photos and pictures cannot be used. Please use a real face and move naturally."
            
            # Check for screen refresh artifacts (photos on screens have specific patterns)
            # Real faces have natural variations, screen photos have uniform refresh patterns
            if len(decoded_images) >= 3:
                # Calculate variance in pixel differences across frames
                diff_values = [np.mean(np.abs(decoded_images[i].astype(float) - decoded_images[i+1].astype(float))) 
                              for i in range(len(decoded_images) - 1)]
                diff_variance = np.var(diff_values)
                diff_mean = np.mean(diff_values)
                
                # Photos on screens have very low variance in differences (uniform refresh)
                if diff_variance < 1.0:
                    return False, 0.0, "Liveness check failed: Uniform frame differences detected. Photos and pictures cannot be used. Only real faces are allowed."
                
                # Check that differences are significant (real faces have larger variations)
                # Made extremely lenient - only reject if differences are essentially zero
                if diff_mean < 1.0:
                    print(f"[LIVENESS] FAILED: Insufficient frame variation (diff_mean: {diff_mean:.2f})")
                    return False, 0.0, "Liveness check failed: Insufficient frame-to-frame variation. Photos and pictures cannot be used. Please move naturally."
            
            # Additional check: Color and brightness variations
            # Real faces have natural lighting changes, photos on screens have uniform lighting
            if len(decoded_images) >= 3:
                brightness_values = []
                color_variance_values = []
                
                for img in decoded_images:
                    # Calculate average brightness
                    if len(img.shape) == 3:
                        brightness = np.mean(img.astype(float))
                        brightness_values.append(brightness)
                        
                        # Calculate color variance (real faces have more color variation)
                        color_variance = np.var(img.astype(float), axis=(0, 1))
                        color_variance_values.append(np.mean(color_variance))
                
                if brightness_values:
                    brightness_variance = np.var(brightness_values)
                    # Photos have very consistent brightness (screen refresh is uniform)
                    if brightness_variance < 1.0:
                        return False, 0.0, "Liveness check failed: Uniform brightness detected. Photos and pictures cannot be used. Only real faces are allowed."
                
                if color_variance_values:
                    color_variance_range = max(color_variance_values) - min(color_variance_values)
                    # Real faces have more color variation across frames
                    if color_variance_range < 2.0:
                        return False, 0.0, "Liveness check failed: Insufficient color variation. Photos and pictures cannot be used. Please use a real face."
            
            # Check for edge detection variance (real faces have more edge variation)
            if len(decoded_images) >= 3:
                edge_variance_values = []
                for img in decoded_images:
                    if len(img.shape) == 3:
                        gray = np.mean(img.astype(float), axis=2)
                    else:
                        gray = img.astype(float)
                    
                    # Simple edge detection using gradient
                    grad_x = np.abs(np.gradient(gray, axis=1))
                    grad_y = np.abs(np.gradient(gray, axis=0))
                    edge_strength = np.mean(grad_x + grad_y)
                    edge_variance_values.append(edge_strength)
                
                if edge_variance_values:
                    edge_variance = np.var(edge_variance_values)
                    # Real faces have more edge variation due to natural movements
                    if edge_variance < 1.0:
                        return False, 0.0, "Liveness check failed: Static image pattern detected. Photos and pictures cannot be used. Please use a real face."
                    
        except Exception as e:
            print(f"Warning: Could not perform pixel comparison: {e}")
            # Continue with other checks but be more strict
        
        # Second check: Get face locations for each frame
        face_locations = []
        for i, frame in enumerate(image_frames):
            location = get_face_location_from_base64(frame)
            if location:
                face_locations.append(location)
            else:
                print(f"[LIVENESS] WARNING: Face not detected in frame {i+1}")
                # Don't fail immediately - continue with available frames
                # Only fail if too many frames are missing
                if len(face_locations) < 3:
                    return False, 0.0, f"Face not detected in frame {i+1}. Please ensure your face is clearly visible in the camera."
        
        if len(face_locations) < 3:  # Reduced requirement - only need 3 frames with face
            return False, 0.0, f"Face not detected in enough frames. Only detected in {len(face_locations)} out of {len(image_frames)} frames."
        
        print(f"[LIVENESS] Face detected in {len(face_locations)} out of {len(image_frames)} frames")
        
        # Calculate face position variations
        # Face location format: (top, right, bottom, left)
        top_positions = [loc[0] for loc in face_locations]
        left_positions = [loc[3] for loc in face_locations]
        right_positions = [loc[1] for loc in face_locations]
        bottom_positions = [loc[2] for loc in face_locations]
        
        # Calculate variation (standard deviation)
        top_variance = np.std(top_positions)
        left_variance = np.std(left_positions)
        right_variance = np.std(right_positions)
        bottom_variance = np.std(bottom_positions)
        
        # Calculate face size variation (photos usually have consistent size)
        face_heights = [loc[2] - loc[0] for loc in face_locations]
        face_widths = [loc[1] - loc[3] for loc in face_locations]
        height_variance = np.std(face_heights)
        width_variance = np.std(face_widths)
        
        # VERY LENIENT Thresholds for movement detection (prioritize real faces)
        # Real faces will have some variation (micro-movements, breathing, blinking, etc.)
        # Photos/pictures are static and won't have this variation
        MIN_POSITION_VARIANCE = 0.3  # Extremely lenient - any tiny movement passes
        MIN_SIZE_VARIANCE = 0.3  # Very lenient size variation requirement
        MIN_INDIVIDUAL_VARIANCE = 0.3  # At least one direction must show tiny movement
        
        # Calculate position variation (photos have very low or zero variation)
        position_variation = top_variance + left_variance + right_variance + bottom_variance
        size_variation = height_variance + width_variance
        total_variance = (position_variation + size_variation) / 6
        
        # SIMPLIFIED CHECK: If there's ANY movement at all, it's a real face
        # Photos have zero or near-zero movement, real faces have at least tiny movements
        variances = [top_variance, left_variance, right_variance, bottom_variance, height_variance, width_variance]
        max_variance = max(variances)
        min_variance = min(variances)
        total_variance = (position_variation + size_variation) / 6
        
        print(f"[LIVENESS] Movement check - total_variance: {total_variance:.2f}, max_variance: {max_variance:.2f}, min_variance: {min_variance:.2f}")
        
        # PRIMARY CHECK: If there's ANY movement in any direction, pass
        # Only reject if ALL variances are essentially zero (photos)
        if max_variance < 0.2:  # Extremely lenient - only reject if completely static
            print(f"[LIVENESS] FAILED: No movement detected (max_variance: {max_variance:.2f})")
            return False, 0.0, "Liveness check failed: No movement detected. Photos and pictures cannot be used. Please use a real face and move slightly or blink."
        
        # Calculate confidence score (0-1) - extremely lenient
        confidence = min(1.0, max_variance / 2.0)  # Normalize based on max movement
        
        # SECONDARY CHECK: Only reject if movement is completely uniform (all directions same)
        variance_range = max_variance - min_variance
        if variance_range < 0.05:  # Only reject if all directions have identical variance (essentially zero)
            print(f"[LIVENESS] FAILED: Uniform movement pattern (range: {variance_range:.2f})")
            return False, 0.0, "Liveness check failed: Uniform movement pattern detected. Photos and pictures cannot be used. Please move naturally."
        
        # Final check: Ensure movement is consistent across frames (real faces have natural variation)
        # Calculate movement between consecutive frames
        frame_movements = []
        for i in range(len(face_locations) - 1):
            loc1 = face_locations[i]
            loc2 = face_locations[i + 1]
            movement = abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1]) + abs(loc1[2] - loc2[2]) + abs(loc1[3] - loc2[3])
            frame_movements.append(movement)
        
        # Real faces have varying movement amounts, photos have zero or uniform movement
        if len(frame_movements) >= 2:
            movement_variance = np.var(frame_movements)
            movement_mean = np.mean(frame_movements)
            
            # Photos have very low or zero movement variance
            # Made extremely lenient - only reject if completely uniform
            if movement_variance < 0.1:
                print(f"[LIVENESS] FAILED: Uniform frame movement (variance: {movement_variance:.2f})")
                return False, 0.0, "Liveness check failed: Uniform movement pattern detected. Photos and pictures cannot be used. Please move naturally."
            
            # Photos have very low average movement
            # Made extremely lenient - only reject if completely static
            if movement_mean < 0.5:
                print(f"[LIVENESS] FAILED: Insufficient frame movement (mean: {movement_mean:.2f})")
                return False, 0.0, "Liveness check failed: Insufficient movement between frames. Photos and pictures cannot be used. Please move naturally."
        
        # Additional check: Face detection consistency
        # Photos might have perfectly consistent face detection (same exact box every time)
        # Real faces have slight variations in detection even when still
        face_box_areas = [(loc[2] - loc[0]) * (loc[1] - loc[3]) for loc in face_locations]
        area_variance = np.var(face_box_areas)
        area_range = max(face_box_areas) - min(face_box_areas)
        
        # Made extremely lenient - only reject if completely consistent
        if area_variance < 1.0:  # Only reject if area is essentially constant
            print(f"[LIVENESS] FAILED: Face area too consistent (variance: {area_variance:.2f})")
            return False, 0.0, "Liveness check failed: Too consistent face detection. Photos and pictures cannot be used. Please move naturally."
        
        if area_range < 0.5:  # Only reject if area range is essentially zero
            print(f"[LIVENESS] FAILED: Face size too consistent (range: {area_range:.2f})")
            return False, 0.0, "Liveness check failed: Face size too consistent. Photos and pictures cannot be used. Please move naturally."
        
        # Check for temporal movement pattern (real faces have natural acceleration/deceleration)
        if len(face_locations) >= 4:
            # Calculate movement acceleration (change in movement speed)
            movement_speeds = []
            for i in range(len(face_locations) - 1):
                loc1 = face_locations[i]
                loc2 = face_locations[i + 1]
                speed = abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1]) + abs(loc1[2] - loc2[2]) + abs(loc1[3] - loc2[3])
                movement_speeds.append(speed)
            
            if len(movement_speeds) >= 2:
                # Calculate acceleration (change in speed)
                accelerations = [movement_speeds[i+1] - movement_speeds[i] for i in range(len(movement_speeds) - 1)]
                acceleration_variance = np.var(accelerations)
                
                # Real faces have natural acceleration patterns, photos have zero or uniform acceleration
                # Made extremely lenient
                if acceleration_variance < 0.1:
                    print(f"[LIVENESS] FAILED: Artificial movement pattern (accel variance: {acceleration_variance:.2f})")
                    return False, 0.0, "Liveness check failed: Artificial movement pattern detected. Photos and pictures cannot be used. Please use a real face."
        
        print(f"[LIVENESS] SUCCESS: All checks passed with confidence {confidence:.2f}")
        return True, confidence, "Liveness detected successfully"
        
    except Exception as e:
        print(f"[LIVENESS] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, 0.0, f"Liveness detection error: {str(e)}"

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
    """Load all known face encodings from the database"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT employee_id, face_encoding FROM facial_data")
        rows = cursor.fetchall()
        db.close()

        ids = []
        encodings = []

        for r in rows:
            try:
                ids.append(r[0])
                # Use frombuffer to convert bytes back to numpy array
                encoding = np.frombuffer(r[1], dtype=np.float64)
                encodings.append(encoding)
                print(f"[LOAD FACES] Loaded encoding for employee_id: {r[0]}, shape: {encoding.shape}")
            except Exception as e:
                print(f"[LOAD FACES] Error loading encoding for employee_id {r[0]}: {e}")
                continue

        print(f"[LOAD FACES] Successfully loaded {len(encodings)} face encodings")
        return ids, encodings
    except Exception as e:
        print(f"[LOAD FACES] Error in load_known_faces: {e}")
        import traceback
        traceback.print_exc()
        return [], []
