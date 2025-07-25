import cv2
import sys
import time

# --- INITIALIZATION ---
print("Connecting to ESP32-CAM...")

## NEW: The URL for our new wireless camera!
stream_url = "http://192.168.1.4:81/stream" 
cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Error: Cannot open stream from ESP32-CAM.")
    sys.exit()

# --- STATE VARIABLES ---
background_frame = None
detection_active = False
motion_detected_first_time = False

delay_seconds = 10
start_time = time.time()

print(f"Connection successful! Detection will begin in {delay_seconds} seconds.")
print("Press 'q' in the video window to exit.")

# --- MAIN LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream ended or failed. Exiting...")
        break
    
    # NOTE: You might not need to flip this frame, as the ESP32 might send it correctly already.
    # You can comment this line out if the video looks backwards.
    # frame = cv2.flip(frame, 1)
    
    # --- The rest of the code is EXACTLY THE SAME ---

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
            print("!!! FIRST MOTION DETECTED! Sending alert... (placeholder)")
            motion_detected_first_time = True

    cv2.imshow('Webcam Monitor', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEAN UP ---
print("Closing application.")
cap.release()
cv2.destroyAllWindows()