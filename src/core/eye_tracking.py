import cv2
import dlib
import numpy as np

class EyeTracking:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("src/models/shape_predictor_68_face_landmarks_GTX.dat")
        self.camera = None
        self.max_score = 100  # Example value, adjust based on your criteria

    def start(self, camera_index):
        self.camera = cv2.VideoCapture(camera_index)

    def stop(self):
        if self.camera and self.camera.isOpened():
            self.camera.release()
            cv2.destroyAllWindows()

    def get_frame(self):
        if self.camera:
            ret, frame = self.camera.read()
            return ret, frame
        return False, None

    def midpoint(self, point1, point2):
        return (int((point1[0] + point2[0]) / 2), int((point1[1] + point2[1]) / 2))

    def get_eye_region(self, landmarks, eye_points):
        return [(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points]

    def get_iris_position(self, eye_region, frame, gray):
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
        threshold = cv2.adaptiveThreshold(eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

        for cnt in contours:
            (x, y, w, h) = cv2.boundingRect(cnt)
            iris_position = (x + int(w / 2), y + int(h / 2))
            return (iris_position[0] + min_x, iris_position[1] + min_y)
        return None

    def get_gaze_data(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        gaze_data = {
            'road_focus': [],
            'mirror_check': [],
            'dashboard_check': [],
            'off_road_gaze': [],
            'prolonged_check': [],
            'closed_eyes': [],
            'gaze_direction': []
        }

        for rect in rects:
            landmarks = self.predictor(gray, rect)

            # Get eye regions
            left_eye_region = self.get_eye_region(landmarks, [36, 37, 38, 39, 40, 41])
            right_eye_region = self.get_eye_region(landmarks, [42, 43, 44, 45, 46, 47])

            left_iris_position = self.get_iris_position(left_eye_region, frame, gray)
            right_iris_position = self.get_iris_position(right_eye_region, frame, gray)

            if left_iris_position and right_iris_position:
                avg_iris_position_x = (left_iris_position[0] + right_iris_position[0]) / 2
                avg_iris_position_y = (left_iris_position[1] + right_iris_position[1]) / 2

                # Calculate eye centers
                left_eye_center = self.midpoint(left_eye_region[0], left_eye_region[3])
                right_eye_center = self.midpoint(right_eye_region[0], right_eye_region[3])
                avg_eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
                avg_eye_center_y = (left_eye_center[1] + right_eye_center[1]) / 2

                # Determine gaze direction
                if avg_iris_position_x < avg_eye_center_x:
                    gaze_direction_x = "Right"
                elif avg_iris_position_x > avg_eye_center_x:
                    gaze_direction_x = "Left"
                else:
                    gaze_direction_x = "Straight"

                if avg_iris_position_y < avg_eye_center_y:
                    gaze_direction_y = "UP"
                elif avg_iris_position_y > avg_eye_center_y:
                    gaze_direction_y = "DOWN"
                else:
                    gaze_direction_y = "Straight"

                gaze_direction = f"{gaze_direction_x}, {gaze_direction_y}"
                gaze_data['gaze_direction'].append(gaze_direction)

        return gaze_data
