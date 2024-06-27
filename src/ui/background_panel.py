# src/ui/background_panel.py
import wx

class BackgroundPanel(wx.Panel):
    def __init__(self, parent, image_path):
        super().__init__(parent)
        self.image_path = image_path
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.draw_background(dc)

    def on_size(self, event):
        self.Refresh()  # Repaint on resize
        event.Skip()

    def draw_background(self, dc):
        client_size = self.GetClientSize()
        image = wx.Image(self.image_path, wx.BITMAP_TYPE_PNG)
        image = image.Scale(client_size.GetWidth(), client_size.GetHeight())
        bitmap = wx.Bitmap(image)
        dc.DrawBitmap(bitmap, 0, 0)