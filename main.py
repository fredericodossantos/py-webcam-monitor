import cv2
import sys
import time
import requests
from datetime import datetime ## NEW: Import the datetime library

# --- CONFIGURATION ---
ESP32_IP = "192.168.1.4" # Make sure this IP is correct
stream_url = f"http://{ESP32_IP}:81/stream"
led_on_url = f"http://{ESP32_IP}/led-on"
led_off_url = f"http://{ESP32_IP}/led-off"

# --- INITIALIZATION ---
print("Connecting to ESP32-CAM...")
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print(f"Error: Cannot open stream from ESP32-CAM at {stream_url}")
    sys.exit()

# --- STATE VARIABLES ---
background_frame = None
detection_active = False
motion_detected_first_time = False
led_is_on = False
first_detection_timestamp = None ## NEW: Variable to store the timestamp

delay_seconds = 10
start_time = time.time()

print(f"Connection successful! Press 'L' to toggle LED. Press 'q' to exit.")

# --- MAIN LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream ended or failed. Exiting...")
        break

    if not detection_active:
        elapsed_time = time.time() - start_time
        if elapsed_time < delay_seconds:
            remaining_time = int(delay_seconds - elapsed_time) + 1
            text = f"Starting in {remaining_time}..."
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            print("Background set. Motion detection is now active.")
            detection_active = True
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            background_frame = cv2.GaussianBlur(gray, (21, 21), 0)

    if detection_active and background_frame is not None:
        has_motion = False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)
        frame_delta = cv2.absdiff(background_frame, gray_blur)
        thresh = cv2.threshold(frame_delta, 30, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            
            has_motion = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Motion Detected", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        
        if has_motion and not motion_detected_first_time:
            ## MODIFIED: Get current time and format it
            now = datetime.now()
            first_detection_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            
            ## MODIFIED: Print the timestamped message
            print(f"!!! FIRST MOTION DETECTED at {first_detection_timestamp} !!!")
            
            motion_detected_first_time = True
            
    ## NEW: If motion has been detected, permanently display the timestamp on screen
    if first_detection_timestamp:
        cv2.putText(frame, f"Alert: {first_detection_timestamp}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # --- KEYBOARD INPUT HANDLING ---
    cv2.imshow('Webcam Monitor', frame)
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
    print("Ensuring LED is off before exit.")
except:
    pass

print("Closing application.")
cap.release()
cv2.destroyAllWindows()