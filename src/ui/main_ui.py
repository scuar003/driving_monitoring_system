import wx
import wx.media
import cv2
import os
import datetime
from core.gaze_detection import EyeTracker
from core.pos_callibartion import perform_calibration
from core.engagement_score import calculate_engagement_score
from utils.database import Database
from utils.user_database import UserDatabase
from ui.background_panel import BackgroundPanel
import logging
import subprocess

logging.basicConfig(level=logging.DEBUG)

class RegistrationDialog(wx.Dialog):
    def __init__(self, parent):
        super(RegistrationDialog, self).__init__(parent, title="Register", size=(400, 400))

        vbox = wx.BoxSizer(wx.VERTICAL)

        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        label_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.first_name_label = wx.StaticText(self, label="First Name:")
        self.first_name_label.SetFont(label_font)
        vbox.Add(self.first_name_label, flag=wx.LEFT | wx.TOP, border=10)
        self.first_name_text = wx.TextCtrl(self, style=wx.BORDER_SIMPLE)
        vbox.Add(self.first_name_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.last_name_label = wx.StaticText(self, label="Last Name:")
        self.last_name_label.SetFont(label_font)
        vbox.Add(self.last_name_label, flag=wx.LEFT | wx.TOP, border=10)
        self.last_name_text = wx.TextCtrl(self, style=wx.BORDER_SIMPLE)
        vbox.Add(self.last_name_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.email_label = wx.StaticText(self, label="Email:")
        self.email_label.SetFont(label_font)
        vbox.Add(self.email_label, flag=wx.LEFT | wx.TOP, border=10)
        self.email_text = wx.TextCtrl(self, style=wx.BORDER_SIMPLE)
        vbox.Add(self.email_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.username_label = wx.StaticText(self, label="Username:")
        self.username_label.SetFont(label_font)
        vbox.Add(self.username_label, flag=wx.LEFT | wx.TOP, border=10)
        self.username_text = wx.TextCtrl(self, style=wx.BORDER_SIMPLE)
        vbox.Add(self.username_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.password_label = wx.StaticText(self, label="Password:")
        self.password_label.SetFont(label_font)
        vbox.Add(self.password_label, flag=wx.LEFT | wx.TOP, border=10)
        self.password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD | wx.BORDER_SIMPLE)
        vbox.Add(self.password_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.register_button = wx.Button(self, label="Register")
        self.register_button.SetFont(font)
        self.register_button.SetBackgroundColour("#2196F3")  # Blue
        self.register_button.SetForegroundColour(wx.WHITE)
        self.register_button.Bind(wx.EVT_BUTTON, self.on_register)
        vbox.Add(self.register_button, flag=wx.ALIGN_CENTER | wx.TOP, border=10)

        self.SetSizerAndFit(vbox)

    def on_register(self, event):
        first_name = self.first_name_text.GetValue()
        last_name = self.last_name_text.GetValue()
        email = self.email_text.GetValue()
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()

        if first_name and last_name and email and username and password:
            if self.GetParent().user_db.create_user(username, password, first_name, last_name, email):
                wx.MessageBox('User registered successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
                self.Close()
            else:
                wx.MessageBox('Username already exists', 'Error', wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox('Please fill in all fields', 'Error', wx.OK | wx.ICON_ERROR)

class LoginFrame(wx.Frame):
    def __init__(self, parent, title):
        super(LoginFrame, self).__init__(parent, title=title, size=(600, 600))
        self.user_db = UserDatabase()
        self.init_ui()

    def init_ui(self):
        panel = BackgroundPanel(self, "data/fiulogo.png")
        vbox = wx.BoxSizer(wx.VERTICAL)

        inner_panel = wx.Panel(panel, style=wx.TRANSPARENT_WINDOW)
        inner_panel.SetBackgroundColour(wx.Colour(255, 255, 255, 150))  # semi-transparent white background

        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        label_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        inner_vbox = wx.BoxSizer(wx.VERTICAL)
        self.username_label = wx.StaticText(inner_panel, label="Username:")
        self.username_label.SetFont(label_font)
        inner_vbox.Add(self.username_label, flag=wx.LEFT | wx.TOP, border=10)

        self.username_text = wx.TextCtrl(inner_panel, style=wx.BORDER_SIMPLE)
        inner_vbox.Add(self.username_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.password_label = wx.StaticText(inner_panel, label="Password:")
        self.password_label.SetFont(label_font)
        inner_vbox.Add(self.password_label, flag=wx.LEFT | wx.TOP, border=10)

        self.password_text = wx.TextCtrl(inner_panel, style=wx.TE_PASSWORD | wx.BORDER_SIMPLE)
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
            if perform_calibration():
                wx.MessageBox('Calibration successful', 'Info', wx.OK | wx.ICON_INFORMATION)
                self.Hide()
                frame = MainFrame(None, "Main App", username)
                frame.Show()
            else:
                wx.MessageBox('Calibration failed', 'Error', wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox('Invalid username or password', 'Error', wx.OK | wx.ICON_ERROR)

    def on_register(self, event):
        dlg = RegistrationDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

class MainFrame(wx.Frame):
    def __init__(self, parent, title, username):
        super(MainFrame, self).__init__(parent, title=f"{title} - Logged in as {username}", size=(800, 600))

        self.username = username
        self.user_db = UserDatabase()
        self.panel = BackgroundPanel(self, "data/fiulogo.png")

        # Initialize video recording variables
        self.video_writer = None
        self.video_file = None

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

        self.dashboard_button = wx.Button(top_button_panel, label="📊 Report ")
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
        self.report_panel = self.create_report_panel()
        self.settings_panel = self.create_settings_panel()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(top_button_panel, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.home_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.profile_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.report_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.settings_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.profile_panel.Hide()
        self.report_panel.Hide()
        self.settings_panel.Hide()

        self.panel.SetSizerAndFit(self.sizer)
        self.predictor_path = "src/models/shape_predictor_68_face_landmarks_GTX.dat"

        self.eye_tracking = EyeTracker(self.predictor_path)
        self.db = Database()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        self.Bind(wx.EVT_CLOSE, self.on_close)  # Bind the close event

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
        layout.Add(self.username_label, 0, wx.ALL | wx.ALIGN_LEFT, 5)  # Align to the left
        layout.Add(self.logout_button, 0, wx.ALL | wx.EXPAND, 5)

        panel.SetSizerAndFit(layout)

        return panel

    def create_profile_panel(self):
        panel = wx.Panel(self.panel, style=wx.TRANSPARENT_WINDOW)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255, 0))  # Transparent background

        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        vbox = wx.BoxSizer(wx.VERTICAL)

        user_info = self.user_db.get_user_info(self.username)

        self.profile_username_label = wx.StaticText(panel, label=f"Username: {self.username}")
        self.profile_username_label.SetFont(font)
        vbox.Add(self.profile_username_label, flag=wx.ALL, border=10)

        self.profile_first_name_label = wx.StaticText(panel, label=f"First Name: {user_info[0]}")
        self.profile_first_name_label.SetFont(font)
        vbox.Add(self.profile_first_name_label, flag=wx.ALL, border=10)

        self.profile_last_name_label = wx.StaticText(panel, label=f"Last Name: {user_info[1]}")
        self.profile_last_name_label.SetFont(font)
        vbox.Add(self.profile_last_name_label, flag=wx.ALL, border=10)

        self.profile_email_label = wx.StaticText(panel, label=f"Email: {user_info[2]}")
        self.profile_email_label.SetFont(font)
        vbox.Add(self.profile_email_label, flag=wx.ALL, border=10)

        self.profile_password_label = wx.StaticText(panel, label="Password: ****")
        self.profile_password_label.SetFont(font)
        vbox.Add(self.profile_password_label, flag=wx.ALL, border=10)

        self.change_password_button = wx.Button(panel, label="Change Password")
        self.change_password_button.SetFont(font)
        self.change_password_button.SetBackgroundColour("#FF9800")  # Orange
        self.change_password_button.SetForegroundColour(wx.WHITE)
        self.change_password_button.Bind(wx.EVT_BUTTON, self.change_password)
        vbox.Add(self.change_password_button, flag=wx.ALL, border=10)

        self.delete_profile_button = wx.Button(panel, label="Delete Profile")
        self.delete_profile_button.SetFont(font)
        self.delete_profile_button.SetBackgroundColour("#FF0000")  # Red
        self.delete_profile_button.SetForegroundColour(wx.WHITE)
        self.delete_profile_button.Bind(wx.EVT_BUTTON, self.delete_profile)
        vbox.Add(self.delete_profile_button, flag=wx.ALL, border=10)

        panel.SetSizerAndFit(vbox)

        return panel

    def create_report_panel(self):
        panel = wx.Panel(self.panel, style=wx.TRANSPARENT_WINDOW)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255, 0))  # Transparent background

        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.video_choice = wx.Choice(panel, choices=self.get_video_files())
        self.video_choice.SetBackgroundColour("#FFD700")  # Gold
        self.video_choice.SetForegroundColour(wx.BLACK)
        self.video_choice.Bind(wx.EVT_CHOICE, self.on_select_video)
        vbox.Add(self.video_choice, flag=wx.LEFT | wx.TOP, border=10)

        self.play_button = wx.Button(panel, label="Play Video")
        self.play_button.SetFont(font)
        self.play_button.SetBackgroundColour("#4CAF50")  # Green
        self.play_button.SetForegroundColour(wx.WHITE)
        self.play_button.Bind(wx.EVT_BUTTON, self.play_video)
        vbox.Add(self.play_button, flag=wx.LEFT | wx.TOP, border=10)

        self.generate_report_button = wx.Button(panel, label="Generate Report")
        self.generate_report_button.SetFont(font)
        self.generate_report_button.SetBackgroundColour("#2196F3")  # Blue
        self.generate_report_button.SetForegroundColour(wx.WHITE)
        self.generate_report_button.Bind(wx.EVT_BUTTON, self.generate_report)
        vbox.Add(self.generate_report_button, flag=wx.LEFT | wx.TOP, border=10)

        panel.SetSizerAndFit(vbox)

        return panel

    def get_video_files(self):
        return [f for f in os.listdir('.') if f.endswith('.avi')]

    def on_select_video(self, event):
        pass  # No action needed here for now

    def play_video(self, event):
        video_file = self.video_choice.GetString(self.video_choice.GetSelection())
        if video_file:
            video_player = VideoPlayer(self, video_file)
            video_player.Show()

    def generate_report(self, event):
        # Get the absolute path of the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        streamlit_app_path = os.path.join(current_dir, 'streamlit_app.py')
    
        if os.path.exists(streamlit_app_path):
            subprocess.Popen(['streamlit', 'run', streamlit_app_path])
        else:
            wx.MessageBox(f"Error: File does not exist: {streamlit_app_path}", 'Error', wx.OK | wx.ICON_ERROR)

    def create_settings_panel(self):
        panel = wx.Panel(self.panel)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # Solid white background

        notebook = wx.Notebook(panel)

        calibrate_panel = wx.Panel(notebook)
        help_panel = wx.Panel(notebook)
        about_us_panel = wx.Panel(notebook)
        privacy_panel = wx.Panel(notebook)

        notebook.AddPage(calibrate_panel, "Calibrate")
        notebook.AddPage(help_panel, "Help")
        notebook.AddPage(about_us_panel, "About Us")
        notebook.AddPage(privacy_panel, "Privacy")

        # Calibrate panel
        calibrate_sizer = wx.BoxSizer(wx.VERTICAL)
        calibrate_text = wx.StaticText(calibrate_panel, label="Calibration settings go here.")
        calibrate_sizer.Add(calibrate_text, 0, wx.ALL, 10)
        calibrate_panel.SetSizer(calibrate_sizer)

        # Help panel
        help_sizer = wx.BoxSizer(wx.VERTICAL)
        help_text = wx.StaticText(help_panel, label="Help information goes here.")
        help_sizer.Add(help_text, 0, wx.ALL, 10)
        help_panel.SetSizer(help_sizer)

        # About Us panel
        about_us_sizer = wx.BoxSizer(wx.VERTICAL)
        mission_text = wx.StaticText(about_us_panel, label="We are a team of 4 from FIU who aim to use this app to help combat driver drowsiness.")
        about_us_sizer.Add(mission_text, 0, wx.ALL, 10)
        contact_text = wx.StaticText(about_us_panel, label=
            "Santiago Cuartas\nPhone: 555-1234\nEmail: santiago@example.com\n\n"
            "Johann Cardentey\nPhone: 555-5678\nEmail: johann@example.com\n\n"
            "Carlos Quintanilla\nPhone: 555-8765\nEmail: carlos@example.com\n\n"
            "Flavio Leguen\nPhone: 555-4321\nEmail: flavio@example.com")
        about_us_sizer.Add(contact_text, 0, wx.ALL, 10)
        about_us_panel.SetSizer(about_us_sizer)

        # Privacy panel
        privacy_sizer = wx.BoxSizer(wx.VERTICAL)
        privacy_text = wx.StaticText(privacy_panel, label="Privacy policy information goes here.")
        privacy_sizer.Add(privacy_text, 0, wx.ALL, 10)
        privacy_panel.SetSizer(privacy_sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        return panel

    def show_home(self, event):
        self.profile_panel.Hide()
        self.report_panel.Hide()
        self.settings_panel.Hide()
        self.home_panel.Show()
        self.panel.Layout()

    def show_profile(self, event):
        self.home_panel.Hide()
        self.report_panel.Hide()
        self.settings_panel.Hide()
        self.profile_panel.Show()
        self.panel.Layout()

    def show_dashboard(self, event):
        self.update_video_files()  # Update the dropdown menu with the latest video files
        self.home_panel.Hide()
        self.profile_panel.Hide()
        self.settings_panel.Hide()
        self.report_panel.Show()
        self.panel.Layout()

    def show_settings(self, event):
        self.home_panel.Hide()
        self.profile_panel.Hide()
        self.report_panel.Hide()
        self.settings_panel.Show()
        self.panel.Layout()

    def change_password(self, event):
        dlg = wx.TextEntryDialog(self, 'Enter new password:', 'Change Password')
        if dlg.ShowModal() == wx.ID_OK:
            new_password = dlg.GetValue()
            self.user_db.change_password(self.username, new_password)
            wx.MessageBox('Password changed successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
        dlg.Destroy()

    def delete_profile(self, event):
        dlg = wx.MessageDialog(self, 'Are you sure you want to delete your profile?', 'Confirm Delete', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            self.user_db.delete_user(self.username)
            wx.MessageBox('Profile deleted successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.logout(event)
        dlg.Destroy()

    def start_live_feed(self, event):
        selected_camera_index = self.camera_choice.GetSelection()
        self.live_feed_button.Disable()
        self.stop_feed_button.Enable()
        calibration_points = ['Top-Left', 'Top-Right', 'Bottom-Left', 'Bottom-Right', 'Left Mirror', 'Right Mirror', 'Rear Mirror', 'Dashboard']
        calibration_data = self.eye_tracking.calibrate(calibration_points)
        self.eye_tracking.start_tracking(calibration_data)
        self.eye_tracking.save_gaze_data("data/gaze_data.csv")

        self.timer.Start(1000 // 30)  # Update frame 30 times per second

        # Start recording video
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_file = f"recording_{timestamp}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(self.video_file, fourcc, 20.0, (640, 480))  # Adjust resolution as needed

    def stop_live_feed(self, event):
        self.timer.Stop()
        self.eye_tracking.stop_tracking()
        self.live_feed_button.Enable()
        self.stop_feed_button.Disable()

        # Stop recording video
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # Update the video files list in the report section
        self.update_video_files()

    def on_video_frame_close(self, event):
        self.stop_live_feed(event)  # Call stop_live_feed when video frame is closed
        event.Skip()  # Ensure the default close event is still processed

    def update_frame(self, event):
        ret, frame = self.eye_tracking.cap.read()
        if ret:
            height, width = frame.shape[:2]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bitmap = wx.Bitmap.FromBuffer(width, height, frame_rgb)

            # Save frame to video file
            if self.video_writer:
                self.video_writer.write(frame)

            gaze_data = self.eye_tracking.gaze_data(frame)
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

    def update_video_files(self):
        video_files = self.get_video_files()
        self.video_choice.SetItems(video_files)

    def on_close(self, event):
        # Close video writer if still open
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # Delete recorded video files
        for video_file in self.get_video_files():
            try:
                os.remove(video_file)
            except PermissionError:
                logging.error(f"Failed to delete {video_file}. It may be in use.")
        self.Destroy()

class VideoFrame(wx.Frame):
    def __init__(self, parent, title):
        super(VideoFrame, self).__init__(parent, title=title, size=(800, 600))
        self.panel = wx.Panel(self)
        self.video_display = wx.StaticBitmap(self.panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.video_display, 1, wx.EXPAND | wx.ALL, 5)
        self.panel.SetSizer(sizer)

class VideoPlayer(wx.Frame):
    def __init__(self, parent, video_file):
        super(VideoPlayer, self).__init__(parent, title="Video Player", size=(800, 600))
        self.panel = wx.Panel(self)
        self.media_ctrl = wx.media.MediaCtrl(self.panel, style=wx.SIMPLE_BORDER, szBackend=wx.media.MEDIABACKEND_DIRECTSHOW)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.media_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.panel.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.video_file = video_file
        self.play_video()

    def play_video(self):
        if self.media_ctrl.Load(self.video_file):
            self.media_ctrl.Play()
        else:
            wx.MessageBox('Unable to load video file', 'Error', wx.OK | wx.ICON_ERROR)

    def on_close(self, event):
        self.media_ctrl.Stop()
        self.Destroy()

