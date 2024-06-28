import wx
import cv2
from core.eye_tracking import EyeTracking
from core.gaze_detection import IrisTracker
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

        self.eye_tracking = IrisTracker()
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
        self.eye_tracking.start_tracking(0)
        self.timer.Start(5000)  # Wait for 5 seconds for each stimulus
    
    def record_data(self, event):
        if self.current_stimulus:
            ret, frame = self.eye_tracking.cap.read()
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
            self.eye_tracking.stop_tracking()
            self.save_calibration_data()
            wx.MessageBox('Calibration complete', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.Hide()
            frame = MainFrame(None, "Main App", self.username)
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
        np.savez('data/calibration_data.npz', X=X, y=y, allow_pickle=True)
    
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
        
        inner_panel = wx.Panel(panel, style=wx.TRANSPARENT_WINDOW)
        inner_panel.SetBackgroundColour(wx.Colour(255, 255, 255, 150))  # semi-transparent white background
        
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        label_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        
        inner_vbox = wx.BoxSizer(wx.VERTICAL)
        self.username_label = wx.StaticText(inner_panel, label="Username:")
        self.username_label.SetFont(label_font)
        inner_vbox.Add(self.username_label, flag=wx.LEFT | wx.TOP, border=10)
        
        self.username_text = wx.TextCtrl(inner_panel)
        inner_vbox.Add(self.username_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.password_label = wx.StaticText(inner_panel, label="Password:")
        self.password_label.SetFont(label_font)
        inner_vbox.Add(self.password_label, flag=wx.LEFT | wx.TOP, border=10)
        
        self.password_text = wx.TextCtrl(inner_panel, style=wx.TE_PASSWORD)
        inner_vbox.Add(self.password_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.login_button = wx.Button(inner_panel, label="Login")
        self.login_button.SetFont(font)
        self.login_button.SetBackgroundColour("#4CAF50")  # Green
        self.login_button.SetForegroundColour(wx.WHITE)
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login)
        inner_vbox.Add(self.login_button, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        self.register_button = wx.Button(inner_panel, label="Register")
        self.register_button.SetFont(font)
        self.register_button.SetBackgroundColour("#2196F3")  # Blue
        self.register_button.SetForegroundColour(wx.WHITE)
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
            frame = MainFrame(None, "Main App", username)
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


class MainFrame(wx.Frame):
    def __init__(self, parent, title, username):
        super(MainFrame, self).__init__(parent, title=f"{title} - Logged in as {username}", size=(800, 600))
        
        self.username = username
        self.panel = BackgroundPanel(self, "data/VisionGuard.png")
        
        # Create top button panel
        top_button_panel = wx.Panel(self.panel, style=wx.TRANSPARENT_WINDOW)
        top_button_panel.SetBackgroundColour("#333333")  # Dark background for the top panel
        top_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        self.home_button = wx.Button(top_button_panel, label="🏠 Home ")
        self.home_button.SetFont(font)
        self.home_button.SetBackgroundColour("#FFD700")  # Gold
        
        self.profile_button = wx.Button(top_button_panel, label="👤 Profile ")
        self.profile_button.SetFont(font)
        self.profile_button.SetBackgroundColour("#FFD700")  # Gold
        
        self.dashboard_button = wx.Button(top_button_panel, label="📊 Dashboard ")
        self.dashboard_button.SetFont(font)
        self.dashboard_button.SetBackgroundColour("#FFD700")  # Gold
        
        self.settings_button = wx.Button(top_button_panel, label="⚙️ Settings")
        self.settings_button.SetFont(font)
        self.settings_button.SetBackgroundColour("#FFD700")  # Gold
        
        top_button_sizer.Add(self.home_button, 1, wx.EXPAND | wx.ALL, 5)
        top_button_sizer.Add(self.profile_button, 1, wx.EXPAND | wx.ALL, 5)
        top_button_sizer.Add(self.dashboard_button, 1, wx.EXPAND | wx.ALL, 5)
        top_button_sizer.Add(self.settings_button, 1, wx.EXPAND | wx.ALL, 5)
        
        top_button_panel.SetSizer(top_button_sizer)
        
        # Bind button events
        self.home_button.Bind(wx.EVT_BUTTON, self.show_home)
        self.profile_button.Bind(wx.EVT_BUTTON, self.show_profile)
        self.dashboard_button.Bind(wx.EVT_BUTTON, self.show_dashboard)
        self.settings_button.Bind(wx.EVT_BUTTON, self.show_settings)
        
        self.home_panel = self.create_home_panel()
        self.profile_panel = self.create_profile_panel()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(top_button_panel, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.home_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.profile_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.profile_panel.Hide()
        
        self.panel.SetSizerAndFit(self.sizer)

        self.eye_tracking = IrisTracker()
        self.db = Database()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)

    def create_home_panel(self):
        panel = wx.Panel(self.panel, style=wx.TRANSPARENT_WINDOW)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255, 0))  # Transparent background
        
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        hbox_camera = wx.BoxSizer(wx.HORIZONTAL)
        self.camera_label = wx.StaticText(panel, label="Select Camera:")
        self.camera_label.SetFont(font)
        self.camera_label.SetBackgroundColour("#FFD700")  # Gold
        self.camera_label.SetForegroundColour(wx.BLACK)
        self.camera_choice = wx.Choice(panel, choices=["Camera 1", "Camera 2"])  # Add more camera options as needed
        self.camera_choice.SetBackgroundColour("#FFD700")  # Gold
        self.camera_choice.SetForegroundColour(wx.BLACK)
        hbox_camera.Add(self.camera_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox_camera.Add(self.camera_choice, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.live_feed_button = wx.Button(panel, label="Start Eye-Tracking")
        self.live_feed_button.SetFont(font)
        self.live_feed_button.SetBackgroundColour("#4CAF50")  # Green
        self.live_feed_button.SetForegroundColour(wx.WHITE)
        self.live_feed_button.Bind(wx.EVT_BUTTON, self.start_live_feed)
        
        self.stop_feed_button = wx.Button(panel, label="Stop Eye-Tracking")
        self.stop_feed_button.SetFont(font)
        self.stop_feed_button.SetBackgroundColour("#F44336")  # Red
        self.stop_feed_button.SetForegroundColour(wx.WHITE)
        self.stop_feed_button.Bind(wx.EVT_BUTTON, self.stop_live_feed)
        self.stop_feed_button.Disable()  # Initially disabled until live feed is started
        hbox_buttons.Add(self.live_feed_button, 1, wx.ALL | wx.EXPAND, 5)
        hbox_buttons.Add(self.stop_feed_button, 1, wx.ALL | wx.EXPAND, 5)

        hbox_main = wx.BoxSizer(wx.HORIZONTAL)
        hbox_main.Add(hbox_camera, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox_main.Add(hbox_buttons, 1, wx.ALL | wx.EXPAND, 5)

        self.username_label = wx.StaticText(panel, label=f"Logged in as: {self.username}")
        self.username_label.SetFont(font)
        self.username_label.SetBackgroundColour("#FFD700")  # Gold
        self.username_label.SetForegroundColour(wx.BLACK)
        
        self.logout_button = wx.Button(panel, label="↪️ Logout")
        self.logout_button.SetFont(font)
        self.logout_button.SetBackgroundColour("#FFD700")  # Gold
        self.logout_button.Bind(wx.EVT_BUTTON, self.logout)
        
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(hbox_main, 0, wx.ALL | wx.EXPAND, 5)
        layout.AddStretchSpacer()
        layout.Add(self.username_label, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        layout.Add(self.logout_button, 0, wx.ALL | wx.EXPAND, 5)
        
        panel.SetSizerAndFit(layout)
        
        return panel

    def create_profile_panel(self):
        panel = wx.Panel(self.panel, style=wx.TRANSPARENT_WINDOW)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255, 0))  # Transparent background
        
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.profile_username_label = wx.StaticText(panel, label=f"Username: {self.username}")
        self.profile_username_label.SetFont(font)
        vbox.Add(self.profile_username_label, flag=wx.ALL, border=10)
        
        self.profile_password_label = wx.StaticText(panel, label="Password: ****")
        self.profile_password_label.SetFont(font)
        vbox.Add(self.profile_password_label, flag=wx.ALL, border=10)
        
        self.change_password_button = wx.Button(panel, label="Change Password")
        self.change_password_button.SetFont(font)
        self.change_password_button.SetBackgroundColour("#FF9800")  # Orange
        self.change_password_button.SetForegroundColour(wx.WHITE)
        self.change_password_button.Bind(wx.EVT_BUTTON, self.change_password)
        vbox.Add(self.change_password_button, flag=wx.ALL, border=10)
        
        panel.SetSizerAndFit(vbox)
        
        return panel

    def show_home(self, event):
        self.profile_panel.Hide()
        self.home_panel.Show()
        self.panel.Layout()
    
    def show_profile(self, event):
        self.home_panel.Hide()
        self.profile_panel.Show()
        self.panel.Layout()
    
    def show_dashboard(self, event):
        pass  # Placeholder for dashboard functionality
    
    def show_settings(self, event):
        pass  # Placeholder for settings functionality
    
    def change_password(self, event):
        dlg = wx.TextEntryDialog(self, 'Enter new password:', 'Change Password')
        if dlg.ShowModal() == wx.ID_OK:
            new_password = dlg.GetValue()
            self.user_db = UserDatabase()
            self.user_db.change_password(self.username, new_password)
            wx.MessageBox('Password changed successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
        dlg.Destroy()

    def start_live_feed(self, event):
        selected_camera_index = self.camera_choice.GetSelection()
        self.live_feed_button.Disable()
        self.stop_feed_button.Enable()
        self.eye_tracking.start_tracking(selected_camera_index)
        
        self.timer.Start(1000 // 30)  # Update frame 30 times per second


    def stop_live_feed(self, event):
        self.timer.Stop()
        self.eye_tracking.stop_tracking()
        self.live_feed_button.Enable()
        self.stop_feed_button.Disable()

    def update_frame(self, event):
        ret, frame = self.eye_tracking.cap.read()
        if ret:
            height, width = frame.shape[:2]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bitmap = wx.Bitmap.FromBuffer(width, height, frame_rgb)
            self.video_frame.video_display.SetBitmap(bitmap)
        
            gaze_data = self.eye_tracking.get_gaze_data(frame)
            if gaze_data:
                logging.debug(f"Gaze data: {gaze_data}")
                flattened_gaze_data = self.flatten_gaze_data(gaze_data)
                logging.debug(f"Flattened gaze data: {flattened_gaze_data}")
                self.db.log_gaze_data(self.username, {'gaze_direction': flattened_gaze_data})
                engagement_percentage = calculate_engagement_score(gaze_data)
                print(f"Engagement Percentage: {engagement_percentage:.2f}%")

    def logout(self, event):
        self.Close()
        login_frame = LoginFrame(None, "Login")
        login_frame.Show()

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

class VideoFrame(wx.Frame):
    def __init__(self, parent, title):
        super(VideoFrame, self).__init__(parent, title=title, size=(800, 600))
        self.panel = wx.Panel(self)
        self.video_display = wx.StaticBitmap(self.panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.video_display, 1, wx.EXPAND | wx.ALL, 5)
        self.panel.SetSizer(sizer)


