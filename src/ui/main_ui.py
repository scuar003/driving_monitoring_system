import wx
import cv2
from core.eye_tracking import EyeTracking
from core.engagement_score import calculate_engagement_score
from utils.database import Database
from utils.user_database import UserDatabase

class LoginFrame(wx.Frame):
    def __init__(self, parent, title):
        super(LoginFrame, self).__init__(parent, title=title, size=(300, 250))
        self.user_db = UserDatabase()
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.username_label = wx.StaticText(panel, label="Username:")
        vbox.Add(self.username_label, flag=wx.LEFT | wx.TOP, border=10)
        
        self.username_text = wx.TextCtrl(panel)
        vbox.Add(self.username_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.password_label = wx.StaticText(panel, label="Password:")
        vbox.Add(self.password_label, flag=wx.LEFT | wx.TOP, border=10)
        
        self.password_text = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        vbox.Add(self.password_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.login_button = wx.Button(panel, label="Login")
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login)
        vbox.Add(self.login_button, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
        self.register_button = wx.Button(panel, label="Register")
        self.register_button.Bind(wx.EVT_BUTTON, self.on_register)
        vbox.Add(self.register_button, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        
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

class CameraApp(wx.Frame):
    def __init__(self, parent, title, username):
        super(CameraApp, self).__init__(parent, title=title, size=(800, 600))
        
        self.username = username
        self.panel = wx.Panel(self)
        
        self.camera_label = wx.StaticText(self.panel, label="Select Camera:")
        self.camera_choice = wx.Choice(self.panel, choices=["Camera 1", "Camera 2"]) # Add more camera options as needed
        
        self.live_feed_button = wx.Button(self.panel, label="Start Eye-Tracking")
        self.live_feed_button.Bind(wx.EVT_BUTTON, self.start_live_feed)
        
        self.stop_feed_button = wx.Button(self.panel, label="Stop Eye-Tracking")
        self.stop_feed_button.Bind(wx.EVT_BUTTON, self.stop_live_feed)
        self.stop_feed_button.Disable() # Initially disabled until live feed is started

        self.video_display = wx.StaticBitmap(self.panel)
        
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.camera_label, 0, wx.ALL, 5)
        self.layout.Add(self.camera_choice, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.live_feed_button, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.stop_feed_button, 0, wx.ALL | wx.EXPAND, 5)
        self.layout.Add(self.video_display, 1, wx.ALL | wx.EXPAND, 5)
        
        self.panel.SetSizerAndFit(self.layout)

        self.eye_tracking = EyeTracking()
        self.db = Database()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        
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
            self.db.log_gaze_data(self.username, gaze_data)
            engagement_percentage = calculate_engagement_score(gaze_data)
            print(f"Engagement Percentage: {engagement_percentage:.2f}%")
