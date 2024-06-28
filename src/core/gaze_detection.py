import cv2
import dlib
import numpy as np

class IrisTracker:
    def __init__(self):
        predictor_path = "src/Models/shape_predictor_68_face_landmarks_GTX.dat"
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        self.cap = None
        self.tracking = False

    def midpoint(self, point1, point2):
        return (int((point1[0] + point2[0]) / 2), int((point1[1] + point2[1]) / 2))

    def get_eye_region(self, landmarks, eye_points):
        return [(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points]

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
        
        scale_factor = 10
        threshold_resized = cv2.resize(eye_masked, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
        cv2.imshow("Threshold", threshold_resized)

        if contours:
            cnt = contours[0]
            (x, y, w, h) = cv2.boundingRect(cnt)
            iris_position = (x + int(w / 2), y + int(h / 2))
            return (iris_position[0] + min_x, iris_position[1] + min_y)
        return None

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        
        for face in faces:
            landmarks = self.predictor(gray, face)
            
            left_eye_region = self.get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
            right_eye_region = self.get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])
            
            left_iris_position = self.get_iris_position(left_eye_region, frame, gray)
            right_iris_position = self.get_iris_position(right_eye_region, frame, gray)

            if left_iris_position and right_iris_position:
                avg_iris_position_x = (left_iris_position[0] + right_iris_position[0]) / 2
                avg_iris_position_y = (left_iris_position[1] + right_iris_position[1]) / 2
                
                cv2.circle(frame, left_iris_position, 2, (0, 255, 0), -1)
                cv2.circle(frame, right_iris_position, 2, (0, 255, 0), -1)
                
                left_eye_center = self.midpoint(left_eye_region[0], left_eye_region[3])
                right_eye_center = self.midpoint(right_eye_region[0], right_eye_region[3])
                avg_eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
                avg_eye_center_y = (left_eye_center[1] + right_eye_center[1]) / 2
                
                if avg_iris_position_x < avg_eye_center_x:
                    gaze_direction_x = "Right"
                elif avg_iris_position_x > avg_eye_center_x:
                    gaze_direction_x = "Left"
                else:
                    gaze_direction_x = "Straight"
                
                if avg_iris_position_y < avg_eye_center_y:
                    gaze_direction_y = "Up"
                elif avg_iris_position_y > avg_eye_center_y:
                    gaze_direction_y = "Down"
                else:
                    gaze_direction_y = "Straight"

                gaze_direction = f"{gaze_direction_x}, {gaze_direction_y}"
                cv2.putText(frame, f"Gaze: {gaze_direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        return frame

    def start_tracking(self, camera_index):
        self.cap = cv2.VideoCapture(camera_index)
        self.tracking = True

        # Create a named window and set its size
        cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Frame", 640, 480)  # Set window size to 640x480

        try:
            while self.tracking:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
                frame = self.process_frame(frame)
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1)
                if key == 27:
                    self.stop_tracking()
                    break
        except Exception as e:
            print(f"Error during tracking: {e}")
        finally:
            self.stop_tracking()

    def stop_tracking(self):
        self.tracking = False
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
