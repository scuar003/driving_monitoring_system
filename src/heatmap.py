import cv2
import dlib
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns

# Load the predictor and the face detector
predictor_path = "src/Models/shape_predictor_68_face_landmarks_GTX.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

def midpoint(point1, point2):
    return (int((point1[0] + point2[0]) / 2), int((point1[1] + point2[1]) / 2))

def get_eye_region(landmarks, eye_points):
    return [(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points]

def get_iris_position(eye_region, frame, gray):
    mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(eye_region, dtype=np.int32)], 255)
    eye = cv2.bitwise_and(gray, gray, mask=mask)
    
    # Extract the bounding box of the eye region
    min_x = np.min(np.array(eye_region)[:, 0])
    max_x = np.max(np.array(eye_region)[:, 0])
    min_y = np.min(np.array(eye_region)[:, 1])
    max_y = np.max(np.array(eye_region)[:, 1])
    eye = eye[min_y:max_y, min_x:max_x]
    
    eye = cv2.equalizeHist(eye)
    # Apply adaptive thresholding
    threshold = cv2.adaptiveThreshold(eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Apply hexagonal mask to keep only the eye region
    mask_eye = mask[min_y:max_y, min_x:max_x]
    eye_masked = cv2.bitwise_and(threshold, threshold, mask=mask_eye)
    
    contours, _ = cv2.findContours(eye_masked, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    
    scale_factor = 10  # Scale factor to enlarge the image
    threshold_resized = cv2.resize(eye_masked, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
    cv2.imshow("Threshold", threshold_resized)

    if contours:
        cnt = contours[0]
        (x, y, w, h) = cv2.boundingRect(cnt)
        iris_position = (x + int(w / 2), y + int(h / 2))
        return (iris_position[0] + min_x, iris_position[1] + min_y)
    return None

def calibrate(calibration_points, detector, predictor):
    calibration_data = []
    cap = cv2.VideoCapture(0)

    for point in calibration_points:
        while True:
            _, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            cv2.putText(frame, f"Look at point: {point}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.imshow("Calibration", frame)
            key = cv2.waitKey(1)
            if key == ord('c'):
                for face in faces:
                    landmarks = predictor(gray, face)
                    left_eye_region = get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
                    right_eye_region = get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])
                    
                    left_iris_position = get_iris_position(left_eye_region, frame, gray)
                    right_iris_position = get_iris_position(right_eye_region, frame, gray)

                    if left_iris_position and right_iris_position:
                        avg_iris_position_x = (left_iris_position[0] + right_iris_position[0]) / 2
                        avg_iris_position_y = (left_iris_position[1] + right_iris_position[1]) / 2

                        left_eye_center = midpoint(left_eye_region[0], left_eye_region[3])
                        right_eye_center = midpoint(right_eye_region[0], right_eye_region[3])
                        avg_eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
                        avg_eye_center_y = (left_eye_center[1] + right_eye_center[1]) / 2
                        # Calculate the new distance to the screen
                        new_distance = calculate_eye_to_screen_distance(left_eye_center, right_eye_center, standard_distance_centers, standard_screen_distance)
            
                        screen_position = map_to_screen((avg_iris_position_x, avg_iris_position_y), (avg_eye_center_x, avg_eye_center_y), new_distance)

                        calibration_data.append((screen_position[0], screen_position[1], point))
                        break
                break

    cap.release()
    cv2.destroyAllWindows()
    return calibration_data

def calculate_eye_to_screen_distance(eye_center_left, eye_center_right, standard_distance_centers, standard_screen_distance):
    new_centers_distance = np.linalg.norm(np.array(eye_center_left) - np.array(eye_center_right))
    new_distance = (standard_distance_centers / new_centers_distance) * standard_screen_distance
    return new_distance

def map_to_screen(iris_position, eye_center, distance):
    # Calculate direction vector
    vector_x = iris_position[0] - eye_center[0]
    vector_y = iris_position[1] - eye_center[1]
    
    # Calculate target positions on the screen using distance scaling
    target_x = iris_position[0] + vector_x * distance
    target_y = iris_position[1] + vector_y * distance
    
    # Normalize target positions to screen coordinates
    screen_x = target_x
    screen_y = target_y
    
    return screen_x, screen_y

def check_screen_position(calibration_data, screen_position):
    # Extract only the x, y coordinates of calibration points
    polygon = np.array([(x, y) for x, y, _ in calibration_data], dtype=np.int32)
    point = (int(screen_position[0]), int(screen_position[1]))
    inside = cv2.pointPolygonTest(polygon, point, False)
    return inside >= 0



# Example calibration points on the screen
# Standard distances for calibration
standard_distance_centers = 80  
standard_screen_distance = 50
calibration_points = [(0, 0), (2560, 0), (0, 1440), (2560, 1440)]
calibration_data = calibrate(calibration_points, detector, predictor)
print("Calibration data:", calibration_data)

# Screen size
screen_size = (2560, 1440)  # Example screen resolution

# Gaze estimation and recording
cap = cv2.VideoCapture(0)
gaze_data = []

while True:
    _, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)
        left_eye_region = get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
        right_eye_region = get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])
        
        left_iris_position = get_iris_position(left_eye_region, frame, gray)
        right_iris_position = get_iris_position(right_eye_region, frame, gray)

        if left_iris_position and right_iris_position:
            avg_iris_position_x = (left_iris_position[0] + right_iris_position[0]) / 2
            avg_iris_position_y = (left_iris_position[1] + right_iris_position[1]) / 2
            
            left_eye_center = midpoint(left_eye_region[0], left_eye_region[3])
            right_eye_center = midpoint(right_eye_region[0], right_eye_region[3])
            avg_eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
            avg_eye_center_y = (left_eye_center[1] + right_eye_center[1]) / 2
            
            # Calculate the new distance to the screen
            new_distance = calculate_eye_to_screen_distance(left_eye_center, right_eye_center, standard_distance_centers, standard_screen_distance)
            
            screen_position = map_to_screen((avg_iris_position_x, avg_iris_position_y), (avg_eye_center_x, avg_eye_center_y), new_distance)
            
            # Convert screen_position to integers
            screen_position_int = (int(screen_position[0]), int(screen_position[1]))
            cv2.circle(frame, left_iris_position, 2, (0, 255, 0), -1)
            cv2.circle(frame, right_iris_position, 2, (0, 255, 0), -1)
            cv2.putText(frame, f"Gaze: {screen_position_int}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Check if the screen position is within the calibration figure
            is_inside = check_screen_position(calibration_data, screen_position_int)
            if is_inside:
                gaze_data.append({"timestamp": time.time(), "screen_x": screen_position_int[0], "screen_y": screen_position_int[1]})
                cv2.circle(frame, screen_position_int, 5, (255, 0, 0), -1)
    
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()

# Save gaze data to a CSV file
gaze_df = pd.DataFrame(gaze_data)
gaze_df.to_csv("data/gaze_data.csv", index=False)

# Plot heatmap
plt.figure(figsize=(10, 6))
sns.kdeplot(x=gaze_df['screen_x'], y=gaze_df['screen_y'], cmap="Reds", shade=True, bw_adjust=0.5)
plt.title("Gaze Heatmap")
plt.xlabel("Screen X")
plt.ylabel("Screen Y")
plt.gca().invert_yaxis()  # Invert y-axis to match screen coordinates
plt.show()
