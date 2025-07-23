import cv2
import sys

# 1. --- INITIALIZATION ---
print("Starting Motion Detector...")

# Open the webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    sys.exit()

# This will hold the first frame of the video to use as our background reference
# We initialize it to None
background_frame = None

print("Webcam opened. Point it at a static background for a moment.")
print("Press 'q' in the video window to exit.")

# --- MAIN LOOP ---
while True:
    # Read a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        break # Exit if we can't get a frame

    # Flip the frame to make it like a mirror
    frame = cv2.flip(frame, 1)

    # 2. --- PRE-PROCESSING THE FRAME ---
    # Convert the color frame to grayscale - motion is easier to detect without color
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply a Gaussian blur to smooth the image and remove noise
    # This helps prevent false positives. (21, 21) is the blur kernel size.
    gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

    # 3. --- SETTING THE BACKGROUND ---
    # If this is the very first frame, we'll save it as the background
    # and skip the rest of the loop.
    if background_frame is None:
        background_frame = gray_blur
        continue

    # 4. --- DETECTING MOTION ---
    # Calculate the absolute difference between the background and the current frame
    frame_delta = cv2.absdiff(background_frame, gray_blur)

    # Apply a threshold. Any pixel difference greater than 30 will be set to 255 (white).
    # All other pixels will be set to 0 (black).
    # This creates a black and white mask of the moving object.
    thresh = cv2.threshold(frame_delta, 30, 255, cv2.THRESH_BINARY)[1]

    # Dilate the thresholded image to fill in any holes or gaps
    thresh = cv2.dilate(thresh, None, iterations=2)

    # 5. --- FINDING AND DRAWING CONTOURS ---
    # Find the contours (outlines) of the white areas in our thresholded image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Loop over each contour found
    for contour in contours:
        # If a contour is too small (likely just noise), ignore it
        if cv2.contourArea(contour) < 500: # You can adjust this value
            continue

        # If the contour is large enough, it's motion!
        # Get the bounding box coordinates for the contour
        (x, y, w, h) = cv2.boundingRect(contour)
        
        # Draw a green rectangle around the moving object on the ORIGINAL color frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Put text on the screen
        cv2.putText(frame, "Motion Detected", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)


    # Display the final frame (with rectangles) in a window
    cv2.imshow('Webcam Monitor', frame)

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEAN UP ---
print("Closing application.")
cap.release()
cv2.destroyAllWindows()