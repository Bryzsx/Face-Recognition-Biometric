"""
Face encoding cache to avoid reloading from database on every request
"""
import threading
import time
from utils.logger import get_logger

logger = get_logger(__name__)

# Cache for face encodings
_face_cache = {
    'employee_ids': [],
    'known_encodings': [],
    'last_updated': 0,
    'lock': threading.Lock()
}

# Cache expires after 5 minutes (300 seconds)
CACHE_TTL = 300


def get_cached_faces():
    """
    Get cached face encodings if available and not expired
    
    Returns:
        tuple: (employee_ids, known_encodings) or (None, None) if cache expired/missing
    """
    with _face_cache['lock']:
        current_time = time.time()
        cache_age = current_time - _face_cache['last_updated']
        
        if cache_age < CACHE_TTL and len(_face_cache['known_encodings']) > 0:
            logger.debug(f"Using cached face encodings (age: {cache_age:.1f}s)")
            return _face_cache['employee_ids'].copy(), _face_cache['known_encodings'].copy()
        
        return None, None


def update_face_cache(employee_ids, known_encodings):
    """
    Update the face encoding cache
    
    Args:
        employee_ids: List of employee IDs
        known_encodings: List of face encodings
    """
    with _face_cache['lock']:
        _face_cache['employee_ids'] = employee_ids.copy() if employee_ids else []
        _face_cache['known_encodings'] = known_encodings.copy() if known_encodings else []
        _face_cache['last_updated'] = time.time()
        logger.debug(f"Face cache updated with {len(known_encodings)} encodings")


def clear_face_cache():
    """Clear the face encoding cache (useful when new employees are added)"""
    with _face_cache['lock']:
        _face_cache['employee_ids'] = []
        _face_cache['known_encodings'] = []
        _face_cache['last_updated'] = 0
        logger.info("Face cache cleared")


def get_cached_or_load_faces():
    """
    Get face encodings from cache if available, otherwise load from database
    
    Returns:
        tuple: (employee_ids, known_encodings)
    """
    # Try cache first
    employee_ids, known_encodings = get_cached_faces()
    
    if employee_ids is not None and known_encodings is not None:
        return employee_ids, known_encodings
    
    # Cache miss or expired - load from database
    logger.debug("Cache miss - loading faces from database")
    import face_utils
    employee_ids, known_encodings = face_utils.load_known_faces()
    
    # Update cache
    if employee_ids and known_encodings:
        update_face_cache(employee_ids, known_encodings)
    
    return employee_ids, known_encodings
