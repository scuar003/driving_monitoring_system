from ui.main_ui import CameraApp
import wx

if __name__ == "__main__":
    app = wx.App(False)
    frame = CameraApp()
    frame.Show(True)
    app.MainLoop()
