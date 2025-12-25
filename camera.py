import cv2

camera = None

def gen_frames():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        success, frame = camera.read()
        if not success:
            break

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )

def get_frame():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    return frame if ret else None

def stop_camera():
    global camera
    if camera:
        camera.release()
        camera = None
