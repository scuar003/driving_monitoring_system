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
        gaze_data = {
            'road_focus': [],
            'mirror_check': [],
            'dashboard_check': [],
            'off_road_gaze': [],
            'prolonged_check': [],
            'closed_eyes': []
        }

        for rect in rects:
            shape = self.predictor(gray, rect)
            shape = np.array([[p.x, p.y] for p in shape.parts()])

            left_eye = shape[42:48]
            right_eye = shape[36:42]

            left_ear = self.eye_aspect_ratio(left_eye)
            right_ear = self.eye_aspect_ratio(right_eye)

            gaze_data['road_focus'].append(left_ear)
            gaze_data['mirror_check'].append(right_ear)
            # Add more logic for other gaze data as required

        return gaze_data

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
