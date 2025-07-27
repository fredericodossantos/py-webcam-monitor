import cv2
import sys
import time
import requests
from datetime import datetime

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
motion_in_progress = False ## NEW: Flag to track if motion is currently happening

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
            # (Countdown logic is unchanged, but we won't display text on the frame)
            pass # We just wait for the delay to pass
        else:
            print("Background set. Motion detection is now active.")
            detection_active = True
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            background_frame = cv2.GaussianBlur(gray, (21, 21), 0)

    if detection_active and background_frame is not None:
        has_motion_this_frame = False # A flag for this specific frame
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)
        frame_delta = cv2.absdiff(background_frame, gray_blur)
        thresh = cv2.threshold(frame_delta, 30, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            
            has_motion_this_frame = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        ## NEW LOGIC: Check for state changes
        
        # If we see motion now, but we didn't see it in the previous frame...
        if has_motion_this_frame and not motion_in_progress:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            print(f"ALERT: Motion detected at {timestamp}")
            motion_in_progress = True # Set the flag to ON

        # If we DON'T see motion now, but we DID see it in the previous frame...
        elif not has_motion_this_frame and motion_in_progress:
            print("--- Scene is quiet again. ---")
            motion_in_progress = False # Reset the flag to OFF
            

    # We always display the video window
    cv2.imshow('Webcam Monitor', frame)
    
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    
    elif key == ord('l'):
        # This LED control logic remains the same
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