import wx
import cv2
from core.eye_tracking import EyeTracking
from core.engagement_score import calculate_engagement_score
from utils.database import Database
from utils.user_database import UserDatabase
from ui.background_panel import BackgroundPanel

from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)

class CalibrationFrame(wx.Frame):
    def __init__(self, parent, title, username):
        super(CalibrationFrame, self).__init__(parent, title=title, size=(800, 600))
        
        self.username = username
        self.panel = wx.Panel(self)
        
        self.instructions_label = wx.StaticText(self.panel, label="Look at the stimuli as instructed")
        self.start_button = wx.Button(self.panel, label="Start Calibration")
        self.start_button.Bind(wx.EVT_BUTTON, self.start_calibration)
        
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.instructions_label, 0, wx.ALL, 5)
        self.layout.Add(self.start_button, 0, wx.ALL | wx.EXPAND, 5)
        
        self.panel.SetSizerAndFit(self.layout)

        self.eye_tracking = EyeTracking()
        self.calibration_data = []
        self.current_stimulus = None
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.record_data, self.timer)

        self.stimulus_mapping = {
            'road': 0,
            'left_mirror': 1,
            'right_mirror': 2
        }

    def start_calibration(self, event):
        self.start_button.Disable()
        self.instructions_label.SetLabel("Look at the road")
        self.current_stimulus = "road"
        self.eye_tracking.start(0)
        self.timer.Start(5000)  # Wait for 5 seconds for each stimulus
    
    def record_data(self, event):
        if self.current_stimulus:
            ret, frame = self.eye_tracking.get_frame()
            if ret:
                gaze_data = self.eye_tracking.get_gaze_data(frame)
                if gaze_data:
                    self.calibration_data.append((self.stimulus_mapping[self.current_stimulus], gaze_data))
                    logging.debug(f"Recorded gaze data for {self.current_stimulus}: {gaze_data}")
        
        if self.current_stimulus == "road":
            self.instructions_label.SetLabel("Look at the left mirror")
            self.current_stimulus = "left_mirror"
        elif self.current_stimulus == "left_mirror":
            self.instructions_label.SetLabel("Look at the right mirror")
            self.current_stimulus = "right_mirror"
        elif self.current_stimulus == "right_mirror":
            self.timer.Stop()
            self.eye_tracking.stop()
            self.save_calibration_data()
            wx.MessageBox('Calibration complete', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.Hide()
            frame = CameraApp(None, "Camera App", self.username)
            frame.Show()
    
    def save_calibration_data(self):
        # Prepare data for the KNeighborsClassifier
        X = []
        y = []
        for stimulus, data in self.calibration_data:
            X.append(data)
            y.append(stimulus)
        X = np.array(X)
        y = np.array(y)
        
        # Save calibration data to a file
        np.savez('calibration_data.npz', X=X, y=y, allow_pickle=True)
    
    def flatten_gaze_data(self, data):
        # Convert the gaze_data dictionary to a flat list of numeric values
        flat_data = []
        for key in data:
            if isinstance(data[key], list):
                flat_data.extend([float(x) for x in data[key]])
            else:
                flat_data.append(float(data[key]))
        return flat_data

class LoginFrame(wx.Frame):
    def __init__(self, parent, title):
        super(LoginFrame, self).__init__(parent, title=title, size=(600, 600))
        self.user_db = UserDatabase()
        self.init_ui()
        
    def init_ui(self):
        panel = BackgroundPanel(self, "data/VisionGuard.png")
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        inner_panel = wx.Panel(panel)
        inner_vbox = wx.BoxSizer(wx.VERTICAL)

        self.username_label = wx.StaticText(inner_panel, label="Username:")
        inner_vbox.Add(self.username_label, flag=wx.LEFT | wx.TOP, border=10)
        
        self.username_text = wx.TextCtrl(inner_panel)
        inner_vbox.Add(self.username_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.password_label = wx.StaticText(inner_panel, label="Password:")
        inner_vbox.Add(self.password_label, flag=wx.LEFT | wx.TOP, border=10)
        
        self.password_text = wx.TextCtrl(inner_panel, style=wx.TE_PASSWORD)
        inner_vbox.Add(self.password_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.login_button = wx.Button(inner_panel, label="Login")
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login)
        inner_vbox.Add(self.login_button, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        self.register_button = wx.Button(inner_panel, label="Register")
        self.register_button.Bind(wx.EVT_BUTTON, self.on_register)
        inner_vbox.Add(self.register_button, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        inner_panel.SetSizer(inner_vbox)
        vbox.Add(inner_panel, flag=wx.EXPAND | wx.ALL, border=20)
        panel.SetSizer(vbox)
        
    def on_login(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        if self.user_db.validate_user(username, password):
            self.Hide()
            frame = CameraApp(None, "Camera App", username)
            frame.Show()
        else:
            wx.MessageBox('Invalid username or password', 'Error', wx.OK | wx.ICON_ERROR)
    
    def on_register(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        if self.user_db.create_user(username, password):
            wx.MessageBox('User registered successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox('Username already exists', 'Error', wx.OK | wx.ICON_ERROR)
    
    def on_register(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        if self.user_db.create_user(username, password):
            wx.MessageBox('User registered successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox('Username already exists', 'Error', wx.OK | wx.ICON_ERROR)

class CameraApp(wx.Frame):
    def __init__(self, parent, title, username):
        super(CameraApp, self).__init__(parent, title=title, size=(800, 600))
        
        self.username = username
        self.panel = BackgroundPanel(self, "data/VisionGuard.png")
        
        self.camera_label = wx.StaticText(self.panel, label="Select Camera:")
        self.camera_choice = wx.Choice(self.panel, choices=["Camera 1", "Camera 2"]) # Add more camera options as needed
        
        self.live_feed_button = wx.Button(self.panel, label="Start Eye-Tracking")
        self.live_feed_button.Bind(wx.EVT_BUTTON, self.start_live_feed)
        
        self.stop_feed_button = wx.Button(self.panel, label="Stop Eye-Tracking")
        self.stop_feed_button.Bind(wx.EVT_BUTTON, self.stop_live_feed)
        self.stop_feed_button.Disable() # Initially disabled until live feed is started

        self.engagement_button = wx.Button(self.panel, label="Calculate Engagement Score")
        self.engagement_button.Bind(wx.EVT_BUTTON, self.calculate_engagement_score)

        self.progress_bar = wx.Gauge(self.panel, range=100, style=wx.GA_HORIZONTAL)

        self.video_display = wx.StaticBitmap(self.panel)
        
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.camera_label, 0, wx.ALL, 5)
        self.layout.Add(self.camera_choice, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.live_feed_button, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.stop_feed_button, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.engagement_button, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.video_display, 1, wx.ALL | wx.EXPAND, 5)
        
        self.panel.SetSizerAndFit(self.layout)

        self.eye_tracking = EyeTracking()
        self.db = Database()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        
        self.calibration_model = self.load_calibration_model()
        self.stimulus_mapping = {
            0: 'road',
            1: 'left_mirror',
            2: 'right_mirror'
        }

    def load_calibration_model(self):
        try:
            data = np.load('calibration_data.npz', allow_pickle=True)
            X = data['X']
            y = data['y']
            model = KNeighborsClassifier(n_neighbors=3)
            model.fit(X, y)
            return model
        except Exception as e:
            wx.MessageBox(f'Failed to load calibration model: {e}', 'Error', wx.OK | wx.ICON_ERROR)
            return None
        
    def start_live_feed(self, event):
        selected_camera_index = self.camera_choice.GetSelection()
        self.eye_tracking.start(selected_camera_index)
        self.live_feed_button.Disable()
        self.stop_feed_button.Enable()
        self.timer.Start(1000 // 30)  # Update frame 30 times per second

    def stop_live_feed(self, event):
        self.timer.Stop()
        self.eye_tracking.stop()
        self.live_feed_button.Enable()
        self.stop_feed_button.Disable()

    def update_frame(self, event):
        ret, frame = self.eye_tracking.get_frame()
        if ret:
            height, width = frame.shape[:2]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bitmap = wx.Bitmap.FromBuffer(width, height, frame_rgb)
            self.video_display.SetBitmap(bitmap)
        
            gaze_data = self.eye_tracking.get_gaze_data(frame)
            if gaze_data:
                logging.debug(f"Gaze data: {gaze_data}")
                flattened_gaze_data = self.flatten_gaze_data(gaze_data)
                logging.debug(f"Flattened gaze data: {flattened_gaze_data}")
                self.db.log_gaze_data(self.username, {'gaze_direction': flattened_gaze_data})

    def calculate_engagement_score(self, event):
        data = self.db.retrieve_gaze_data()
        if data:
            flattened_gaze_data = [item[2] for item in data]  # Extract gaze direction data
            engagement_score = calculate_engagement_score(flattened_gaze_data)
            self.update_progress_bar(engagement_score)
            wx.MessageBox(f'Engagement Score: {engagement_score:.2f}%', 'Engagement Score', wx.OK | wx.ICON_INFORMATION)

    def update_progress_bar(self, score):
        self.progress_bar.SetValue(int(score))

    def flatten_gaze_data(self, data):
        flat_data = []
        if isinstance(data, list):
            return data
        try:
            for key in data:
                if isinstance(data[key], list):
                    flat_data.extend([float(x) for x in data[key]])
                else:
                    flat_data.append(float(data[key]))
        except TypeError as e:
            logging.error(f"Error flattening data: {e}")
        return flat_data


