import cv2
import dlib

# Initialize the camera
cap = cv2.VideoCapture(0)

# Load Dlib's face detector and shape predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("src/models/shape_predictor_68_face_landmarks_GTX.dat")

# Define the desired range for the important features (e.g., eyes, nose, mouth)
# You can adjust these values based on your specific requirements
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

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    landmarks = get_face_landmarks(gray, detector, predictor)
    position = check_position(landmarks)

    if position == "Good":
        cv2.putText(frame, "Good Position", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 5)
    else:
        cv2.putText(frame, "Bad Position", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
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
