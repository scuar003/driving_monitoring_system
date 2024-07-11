# src/core/pos_calibration.py
import cv2
import dlib
import time

# Initialize the camera
cap = cv2.VideoCapture(0)

# Load Dlib's face detector and shape predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("src/models/shape_predictor_68_face_landmarks_GTX.dat")

# Define the desired range for the important features (e.g., eyes, nose, mouth)
min_eye_distance = 40
max_eye_distance = 100
min_face_size = 100
max_face_size = 300

def get_face_landmarks(gray, detector, predictor):
    faces = detector(gray)
    for face in faces:
        landmarks = predictor(gray, face)
        return landmarks
    return None

def check_position(landmarks):
    if landmarks:
        left_eye = landmarks.part(36)
        right_eye = landmarks.part(45)
        eye_distance = ((left_eye.x - right_eye.x) ** 2 + (left_eye.y - right_eye.y) ** 2) ** 0.5

        face_width = landmarks.part(16).x - landmarks.part(0).x

        if min_eye_distance < eye_distance < max_eye_distance and min_face_size < face_width < max_face_size:
            return "Good"
    return "Bad"

def draw_loading_circle(frame, center, radius, progress, color):
    start_angle = 0
    end_angle = int(360 * progress)
    cv2.ellipse(frame, center, (radius, radius), 0, start_angle, end_angle, color, thickness=5)

def draw_x(frame, center, size, color):
    x1 = (center[0] - size, center[1] - size)
    x2 = (center[0] + size, center[1] + size)
    x3 = (center[0] - size, center[1] + size)
    x4 = (center[0] + size, center[1] - size)
    cv2.line(frame, x1, x2, color, thickness=5)
    cv2.line(frame, x3, x4, color, thickness=5)

def perform_calibration():
    start_time = None
    duration = 5  # seconds
    center = (50, 50)
    radius = 20
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        landmarks = get_face_landmarks(gray, detector, predictor)
        position = check_position(landmarks)

        if position == "Good":
            if start_time is None:
                start_time = time.time()
            elapsed_time = time.time() - start_time
            progress = min(elapsed_time / duration, 1.0)
            draw_loading_circle(frame, center, radius, progress, (0, 255, 0))
            cv2.putText(frame, "Good Position", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 5)
            if elapsed_time >= duration:
                cap.release()
                cv2.destroyAllWindows()
                return True
        else:
            start_time = None
            draw_x(frame, center, radius, (0, 0, 255))
            cv2.putText(frame, "Bad Position", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 5)

        if landmarks:
            for n in range(0, 68):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)

        cv2.imshow("Calibration", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False
