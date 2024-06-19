import wx
from ui.main_ui import LoginFrame

if __name__ == "__main__":
    app = wx.App(False)
    login = LoginFrame(None, "Login")
    login.Show()
    app.MainLoop()
