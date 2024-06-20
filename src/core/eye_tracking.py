import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist

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

    def get_gaze_data(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        gaze_data = []

        for rect in rects:
            shape = self.predictor(gray, rect)
            shape = np.array([[p.x, p.y] for p in shape.parts()])

            left_eye = shape[42:48]
            right_eye = shape[36:42]

            left_ear = self.eye_aspect_ratio(left_eye)
            right_ear = self.eye_aspect_ratio(right_eye)

            left_gaze_ratio = self.get_gaze_ratio(left_eye, gray)
            right_gaze_ratio = self.get_gaze_ratio(right_eye, gray)

            if left_gaze_ratio and right_gaze_ratio:
                gaze_data.extend([left_ear, right_ear])
                gaze_data.extend(left_gaze_ratio)
                gaze_data.extend(right_gaze_ratio)

        return gaze_data

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def get_gaze_ratio(self, eye, gray):
        mask = np.zeros_like(gray)
        cv2.fillConvexPoly(mask, np.array(eye, dtype=np.int32), 255)
        eye_region = cv2.bitwise_and(gray, gray, mask=mask)

        min_x = np.min(eye[:, 0])
        max_x = np.max(eye[:, 0])
        min_y = np.min(eye[:, 1])
        max_y = np.max(eye[:, 1])
        eye_region = eye_region[min_y:max_y, min_x:max_x]

        if eye_region.size == 0:
            return None

        _, threshold_eye = cv2.threshold(eye_region, 70, 255, cv2.THRESH_BINARY)
        if threshold_eye is None or threshold_eye.size == 0:
            return None

        height, width = threshold_eye.shape

        left_side_threshold = threshold_eye[0:height, 0:int(width / 2)]
        left_side_white = cv2.countNonZero(left_side_threshold)

        right_side_threshold = threshold_eye[0:height, int(width / 2):width]
        right_side_white = cv2.countNonZero(right_side_threshold)

        if right_side_white != 0:
            gaze_ratio_horizontal = left_side_white / right_side_white
        else:
            gaze_ratio_horizontal = left_side_white

        top_side_threshold = threshold_eye[0:int(height / 2), 0:width]
        top_side_white = cv2.countNonZero(top_side_threshold)

        bottom_side_threshold = threshold_eye[int(height / 2):height, 0:width]
        bottom_side_white = cv2.countNonZero(bottom_side_threshold)

        if bottom_side_white != 0:
            gaze_ratio_vertical = top_side_white / bottom_side_white
        else:
            gaze_ratio_vertical = top_side_white

        return gaze_ratio_horizontal, gaze_ratio_vertical
