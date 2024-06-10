import wx
import cv2
from core.eye_tracking import EyeTracking
from core.engagement_score import calculate_engagement_score, calculate_engagement_percentage
from utils.database import Database

class CameraApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Camera App", size=(800, 600))
        
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
            self.db.log_gaze_data(gaze_data)
            engagement_score = calculate_engagement_score(gaze_data)
            engagement_percentage = calculate_engagement_percentage(engagement_score, self.eye_tracking.max_score)
            print(f"Engagement Percentage: {engagement_percentage:.2f}%")
        
if __name__ == "__main__":
    app = wx.App(False)
    frame = CameraApp()
    frame.Show(True)
    app.MainLoop()
