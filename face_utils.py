import cv2
import face_recognition
import pickle

def get_face_encoding(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    enc = face_recognition.face_encodings(rgb)
    return enc[0] if enc else None

def encode_to_blob(encoding):
    return pickle.dumps(encoding)

def decode_from_blob(blob):
    return pickle.loads(blob)
