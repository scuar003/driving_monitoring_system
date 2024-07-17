import cv2
import dlib
import numpy as np
import pandas as pd
import time
import os
from playsound import playsound

class EyeTracker:
    def __init__(self, predictor_path, video_source=0):
        self.predictor_path = predictor_path
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        self.cap = cv2.VideoCapture(video_source)
        self.gaze_data = []
        self.start_time = time.time()
        self.missing_eye_start_time = None
        self.standard_distance_centers = None
        self.standard_screen_distance = 50
        self.alert_sound_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'alert_sound.wav')


    def midpoint(self, point1, point2):
        return (int((point1[0] + point2[0]) / 2), int((point1[1] + point2[1]) / 2))

    def get_eye_region(self, landmarks, eye_points):
        return [(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points]

    def get_eye_center(self, landmarks, eye_points):
        eye_region = [(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points]
        eye_center = self.midpoint(eye_region[0], eye_region[3])
        return eye_center

    def get_iris_position(self, eye_region, frame, gray):
        mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        cv2.fillPoly(mask, [np.array(eye_region, dtype=np.int32)], 255)
        eye = cv2.bitwise_and(gray, gray, mask=mask)
        
        min_x = np.min(np.array(eye_region)[:, 0])
        max_x = np.max(np.array(eye_region)[:, 0])
        min_y = np.min(np.array(eye_region)[:, 1])
        max_y = np.max(np.array(eye_region)[:, 1])
        eye = eye[min_y:max_y, min_x:max_x]
        
        eye = cv2.equalizeHist(eye)
        threshold = cv2.adaptiveThreshold(eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        mask_eye = mask[min_y:max_y, min_x:max_x]
        eye_masked = cv2.bitwise_and(threshold, threshold, mask=mask_eye)
        
        contours, _ = cv2.findContours(eye_masked, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

        if contours:
            cnt = contours[0]
            (x, y, w, h) = cv2.boundingRect(cnt)
            iris_position = (x + int(w / 2), y + int(h / 2))
            return (iris_position[0] + min_x, iris_position[1] + min_y)
        return None

    def get_eye_to_eye_distance(self):
        while True:
            _, frame = self.cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray)
            
            for face in faces:
                landmarks = self.predictor(gray, face)
                left_eye_center = self.get_eye_center(landmarks, [36, 37, 38, 39, 40, 41])
                right_eye_center = self.get_eye_center(landmarks, [42, 43, 44, 45, 46, 47])
                eye_distance_pixels = np.linalg.norm(np.array(left_eye_center) - np.array(right_eye_center))
                
                cv2.circle(frame, left_eye_center, 2, (0, 255, 0), -1)
                cv2.circle(frame, right_eye_center, 2, (0, 255, 0), -1)
                cv2.putText(frame, "Stand around 50 cm from the camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(frame, f"Eye Distance: {eye_distance_pixels:.2f} pixels", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1)
            if key == ord('c'):
                break
        return eye_distance_pixels

    def calibrate(self, calibration_points):
        calibration_data = []
        self.standard_distance_centers = self.get_eye_to_eye_distance()

        for point in calibration_points:
            while True:
                _, frame = self.cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector(gray)
                cv2.putText(frame, f"Look at point: {point}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.imshow("Calibration", frame)
                key = cv2.waitKey(1)
                if key == ord('c'):
                    for face in faces:
                        landmarks = self.predictor(gray, face)
                        left_eye_region = self.get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
                        right_eye_region = self.get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])
                        
                        left_iris_position = self.get_iris_position(left_eye_region, frame, gray)
                        right_iris_position = self.get_iris_position(right_eye_region, frame, gray)

                        if left_iris_position and right_iris_position:
                            avg_iris_position_x = (left_iris_position[0] + right_iris_position[0]) / 2
                            avg_iris_position_y = (left_iris_position[1] + right_iris_position[1]) / 2

                            left_eye_center = self.midpoint(left_eye_region[0], left_eye_region[3])
                            right_eye_center = self.midpoint(right_eye_region[0], right_eye_region[3])
                            avg_eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
                            avg_eye_center_y = (left_eye_center[1] + right_eye_center[1]) / 2

                            new_distance = self.calculate_eye_to_screen_distance(left_eye_center, right_eye_center, self.standard_distance_centers, self.standard_screen_distance)
                            screen_position = self.map_to_screen((avg_iris_position_x, avg_iris_position_y), (avg_eye_center_x, avg_eye_center_y), new_distance)

                            calibration_data.append((screen_position[0], screen_position[1], point))
                            break
                    break
        cv2.destroyAllWindows()
        return calibration_data

    def calculate_eye_to_screen_distance(self, eye_center_left, eye_center_right, standard_distance_centers, standard_screen_distance):
        new_centers_distance = np.linalg.norm(np.array(eye_center_left) - np.array(eye_center_right))
        new_distance = (standard_distance_centers / new_centers_distance) * standard_screen_distance
        return new_distance

    def map_to_screen(self, iris_position, eye_center, distance):
        vector_x = iris_position[0] - eye_center[0]
        vector_y = iris_position[1] - eye_center[1]
        target_x = iris_position[0] + vector_x * distance
        target_y = iris_position[1] + vector_y * distance
        return target_x, target_y

    def check_screen_position(self, calibration_data, screen_position):
        screen_points = calibration_data[0:4]
        polygon = np.array([(x, y) for x, y, _ in screen_points], dtype=np.int32)
        point = (int(screen_position[0]), int(screen_position[1]))
        inside = cv2.pointPolygonTest(polygon, point, False)
        return inside >= 0

    def check_calibration_points(self, calibration_data, screen_position, tolerance=45):
        fixed_points = [point for point in calibration_data if point[2] in ['Left Mirror', 'Right Mirror', 'Rear Mirror', 'Dashboard']]
        closest_point = None
        min_distance = float('inf')

        for point in fixed_points:
            distance = np.linalg.norm(np.array(screen_position) - np.array(point[:2]))
            if distance < min_distance:
                min_distance = distance
                closest_point = point[2]

        if min_distance <= tolerance:
            return closest_point
        else:
            return None

    def start_tracking(self, calibration_data):
        while True:
            _, frame = self.cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray)
            eyes_detected = False

            for face in faces:
                landmarks = self.predictor(gray, face)
                left_eye_region = self.get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
                right_eye_region = self.get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])
                
                left_iris_position = self.get_iris_position(left_eye_region, frame, gray)
                right_iris_position = self.get_iris_position(right_eye_region, frame, gray)

                if left_iris_position and right_iris_position:
                    avg_iris_position_x = (left_iris_position[0] + right_iris_position[0]) / 2
                    avg_iris_position_y = (left_iris_position[1] + right_iris_position[1]) / 2
                    
                    left_eye_center = self.midpoint(left_eye_region[0], left_eye_region[3])
                    right_eye_center = self.midpoint(right_eye_region[0], right_eye_region[3])
                    avg_eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
                    avg_eye_center_y = (left_eye_center[1] + right_eye_center[1]) / 2
                    
                    new_distance = self.calculate_eye_to_screen_distance(left_eye_center, right_eye_center, self.standard_distance_centers, self.standard_screen_distance)
                    screen_position = self.map_to_screen((avg_iris_position_x, avg_iris_position_y), (avg_eye_center_x, avg_eye_center_y), new_distance)
                    
                    screen_position_int = (int(screen_position[0]), int(screen_position[1]))
                    cv2.circle(frame, left_iris_position, 2, (0, 255, 0), -1)
                    cv2.circle(frame, right_iris_position, 2, (0, 255, 0), -1)
                    cv2.putText(frame, f"Gaze: {screen_position_int}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    is_inside = self.check_screen_position(calibration_data, screen_position_int)
                    if is_inside:
                        self.gaze_data.append({"timestamp": time.time()-self.start_time, "screen_x": screen_position_int[0], "screen_y": screen_position_int[1]})
                        cv2.circle(frame, screen_position_int, 5, (255, 0, 0), -1)
                    else:
                        fixed_point = self.check_calibration_points(calibration_data, screen_position_int)
                        if fixed_point:
                            self.gaze_data.append({"timestamp": time.time()-self.start_time, "fixed_point": fixed_point})
                            cv2.putText(frame, f"Looking at: {fixed_point}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    eyes_detected = True

            if not eyes_detected:
                if self.missing_eye_start_time is None:
                    self.missing_eye_start_time = time.time()
                elif time.time() - self.missing_eye_start_time >= 3:
                    cv2.putText(frame, "LOOK AT THE ROAD", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    if time.time() - self.missing_eye_start_time >= 5:
                        playsound(self.alert_sound_path)
            else:
                self.missing_eye_start_time = None
            
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1)
            if key == 27:
                break

    def save_gaze_data(self, file_path):
        gaze_df = pd.DataFrame(self.gaze_data)
        gaze_df.to_csv(file_path, index=False)

    def stop_tracking(self):
        self.tracking = False
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()

    



