# Liveness Detection Feature

## Overview
The Face Biometric System now includes **Liveness Detection** to prevent spoofing attacks using photos or videos. This feature ensures that only real, live faces can be used for attendance.

## How It Works

### Backend (Python)
- The `detect_liveness()` function in `face_utils.py` analyzes multiple frames to detect:
  - **Frame Similarity**: Photos show identical or nearly identical frames
  - **Movement Patterns**: Real faces have natural micro-movements (breathing, blinking, slight head movements)
  - **Brightness & Color Variations**: Real faces have natural lighting changes
  - **Edge Detection**: Real faces have more edge variation than static photos
  
### Frontend (JavaScript)
- Captures **3 frames** at **200ms intervals** (~0.6 seconds total)
- Sends frames to `/api/recognize-face` endpoint
- Shows status messages: "Capturing frames..." → "Checking liveness..." → "Recognizing face..."

### Performance Optimizations
1. **Reduced Frame Count**: 3 frames instead of 5 (40% faster)
2. **Image Resizing**: 320x240 resolution (4x faster than 640x480)
3. **JPEG Compression**: Quality set to 0.7 for faster transmission

## Configuration

Edit `config.py` to customize liveness detection:

```python
# Enable/disable liveness detection
LIVENESS_DETECTION_ENABLED = True  # Set to False to disable

# Minimum frames required for liveness check
LIVENESS_MIN_FRAMES = 3  # Increase for stricter detection

# Interval between frame captures (milliseconds)
LIVENESS_FRAME_INTERVAL_MS = 200  # Increase for slower capture
```

Or use environment variables:
```bash
export LIVENESS_DETECTION_ENABLED=True
export LIVENESS_MIN_FRAMES=3
export LIVENESS_FRAME_INTERVAL_MS=200
```

## Testing

### Test with Real Face (Should PASS)
1. Open the employee attendance page
2. Position your face in the camera
3. The system will capture 3 frames automatically
4. You should see: "Checking liveness..." → "Recognizing face..." → Success!

### Test with Photo (Should FAIL)
1. Take a photo of yourself or display a photo on another screen
2. Point the camera at the photo
3. The system will detect it's a photo and show an error:
   - "Liveness check failed: Frames too similar"
   - "Liveness check failed: No movement detected"
   - "Photos and pictures cannot be used. Only real faces are allowed."

## Expected Performance

- **Capture Time**: ~0.6 seconds (3 frames × 200ms)
- **Liveness Check**: ~0.5-1.0 second (server-side)
- **Total Added Time**: ~1.5 seconds

This is a reasonable trade-off for significantly improved security.

## Troubleshooting

### "Liveness check failed" for real face
- **Solution**: Ensure good lighting and move your head slightly during capture
- **Alternative**: Reduce `LIVENESS_MIN_FRAMES` to 2 in config.py

### Timeout errors
- **Solution**: Increase timeout in `employee_attendance.html` (currently 15 seconds)
- **Check**: Server performance and network speed

### Disable liveness detection temporarily
Set in `config.py`:
```python
LIVENESS_DETECTION_ENABLED = False
```

The system will fall back to single-frame recognition (faster but less secure).

## Security Benefits

✅ **Prevents Photo Spoofing**: Cannot use printed photos  
✅ **Prevents Screen Spoofing**: Cannot use photos displayed on phones/tablets  
✅ **Prevents Video Spoofing**: Detects static video frames  
✅ **Natural User Experience**: No need for user to perform specific actions (blink, smile, etc.)

## Technical Details

### API Changes
The `/api/recognize-face` endpoint now accepts:
```json
{
  "frames": ["data:image/jpeg;base64,...", "data:image/jpeg;base64,...", "data:image/jpeg;base64,..."]
}
```

Backward compatible: Still accepts single `image` parameter for non-liveness mode.

### Response on Liveness Failure
```json
{
  "success": false,
  "message": "Liveness check failed: [specific reason]. Photos and pictures cannot be used. Only real faces are allowed."
}
```
