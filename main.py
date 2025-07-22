import cv2
import sys

# 1. Initialize the webcam
print("Attempting to open webcam...")
cap = cv2.VideoCapture(0) # 0 is the default camera

# 2. Check if the webcam opened correctly
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    sys.exit()

print("Webcam opened successfully! Press 'q' in the video window to exit.")

# 3. Loop to capture and display frames
while True:
    # Read a frame from the webcam
    ret, frame = cap.read()
    
    # If a frame wasn't captured correctly (e.g., webcam disconnected), 'ret' is False
    if not ret:
        print("Error: Can't receive frame. Exiting...")
        break
    
    # Flip the frame horizontally - makes it feel like a mirror
    frame = cv2.flip(frame, 1)

    # Display the resulting frame in a window called "Webcam Monitor"
    cv2.imshow('Webcam Monitor', frame)
    
    # 4. Wait 1ms for the user to press a key. If it's 'q', exit the loop.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. Clean up when the loop ends
print("Closing webcam and destroying windows.")
cap.release()
cv2.destroyAllWindows()