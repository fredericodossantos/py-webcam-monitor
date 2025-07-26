import cv2
import sys
import time
import requests # We will use this for the LED control

# --- CONFIGURATION ---
ESP32_IP = "192.168.1.4" ## NEW: Made the IP a variable for easy access
stream_url = f"http://{ESP32_IP}:81/stream"
control_url = f"http://{ESP32_IP}/control" ## NEW: The URL for sending commands

# --- INITIALIZATION ---
print("Connecting to ESP32-CAM...")
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print("Error: Cannot open stream from ESP32-CAM.")
    sys.exit()

# --- STATE VARIABLES ---
background_frame = None
detection_active = False
motion_detected_first_time = False
led_is_on = False ## NEW: A flag to track the LED's state

delay_seconds = 10
start_time = time.time()

print(f"Connection successful! Press 'L' to toggle the LED. Press 'q' to exit.")

# --- MAIN LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream ended or failed. Exiting...")
        break

    # --- The rest of the logic remains the same ---
    # ... (all the countdown and motion detection code is here) ...
    # ... (I've hidden it for brevity, but it should remain in your file) ...
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
            if cv2.contourArea(contour) < 500: continue
            has_motion = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Motion Detected", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        
        # ... (first motion detection logic remains) ...
        if has_motion and not motion_detected_first_time:
            print("!!! FIRST MOTION DETECTED!")
            motion_detected_first_time = True

    # --- KEYBOARD INPUT HANDLING ---
    cv2.imshow('Webcam Monitor', frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    
    ## NEW: Check if the 'L' key was pressed
    elif key == ord('l'):
        # Toggle the LED state
        led_is_on = not led_is_on 
        
        # Set the value to send (1 for ON, 0 for OFF)
        led_value = 1 if led_is_on else 0
        
        try:
            # Send the command to the ESP32
            requests.get(control_url, params={'var':'flash_led', 'val':led_value}, timeout=2)
            print(f"LED turned {'ON' if led_is_on else 'OFF'}")
        except Exception as e:
            print(f"Error sending LED command: {e}")

# --- CLEAN UP ---
# Turn the LED off before exiting, just in case
try:
    requests.get(control_url, params={'var':'flash_led', 'val':0}, timeout=2)
    print("Ensuring LED is off before exit.")
except:
    pass

print("Closing application.")
cap.release()
cv2.destroyAllWindows()