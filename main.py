import cv2
import sys
import time
import requests
from datetime import datetime

# --- CONFIGURATION ---
ESP32_IP = "192.168.1.4" # Make sure this IP is correct
stream_url = f"http://{ESP32_IP}:81/stream"
# We are keeping the LED control, so these URLs remain
led_on_url = f"http://{ESP32_IP}/led-on"
led_off_url = f"http://{ESP32_IP}/led-off"

# --- INITIALIZATION ---
print("Connecting to ESP32-CAM...")
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print(f"Error: Cannot open stream from ESP32-CAM at {stream_url}")
    sys.exit()

## NEW: Initialize the HOG Person Detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
print("HOG Person Detector initialized.")

# --- STATE VARIABLES ---
led_is_on = False

print("System is active. Press 'L' to toggle LED. Press 'q' to exit.")

# --- MAIN LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream ended or failed. Exiting...")
        break
    
    # Optional: Resize the frame to make processing faster
    # HOG can be slow on very large images.
    frame = cv2.resize(frame, (640, 480))

    ## MODIFIED: This is our new detection logic
    # detectMultiScale returns the bounding boxes of detected people
    boxes, weights = hog.detectMultiScale(frame, winStride=(8,8), padding=(32,32), scale=1.05)

    # If at least one person was detected in this frame
    if len(boxes) > 0:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"PERSON DETECTED at {timestamp}")

        # Draw a green rectangle around each detected person
        for (x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)


    # --- Display the video and handle keyboard input ---
    cv2.imshow('Person Detector', frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    
    elif key == ord('l'):
        led_is_on = not led_is_on
        target_url = led_on_url if led_is_on else led_off_url
        try:
            requests.get(target_url, timeout=2)
            print(f"LED command sent: {'ON' if led_is_on else 'OFF'}")
        except Exception as e:
            print(f"Error sending LED command: {e}")

# --- CLEAN UP ---
try:
    requests.get(led_off_url, timeout=2)
except:
    pass

print("Closing application.")
cap.release()
cv2.destroyAllWindows()