"""
AEGIS AI - Modern Dark-Themed UI Components for Kivy
"""
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

# Theme Color Palette
COLORS = {
    "bg_dark": (0.043, 0.059, 0.098, 1.0),       # #0B0F19
    "card_bg": (0.067, 0.094, 0.153, 1.0),       # #111827
    "card_hover": (0.118, 0.161, 0.235, 1.0),    # #1E293B
    "card_border": (0.122, 0.161, 0.216, 1.0),   # #1F2937
    "primary": (0.063, 0.725, 0.506, 1.0),       # Emerald #10B981
    "primary_dark": (0.02, 0.53, 0.36, 1.0),
    "danger": (0.937, 0.267, 0.267, 1.0),        # Crimson #EF4444
    "warning": (0.961, 0.620, 0.043, 1.0),       # Amber #F59E0B
    "info": (0.231, 0.510, 0.965, 1.0),          # Blue #3B82F6
    "text_main": (0.953, 0.957, 0.965, 1.0),     # #F3F4F6
    "text_muted": (0.612, 0.639, 0.686, 1.0),    # #9CA3AF
    "sidebar_bg": (0.055, 0.075, 0.125, 1.0),
    "input_bg": (0.09, 0.12, 0.18, 1.0),
    "input_border": (0.2, 0.25, 0.35, 1.0)
}

class CyberCard(BoxLayout):
    """Container with rounded dark corners and subtle border"""
    def __init__(self, bg_color=None, border_color=None, radius=8, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color or COLORS["card_bg"]
        self.border_color = border_color or COLORS["card_border"]
        self.radius = radius
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius)])
            Color(*self.border_color)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(self.radius)], width=1.1)

class StatCard(CyberCard):
    """Telemetry Card displaying a metric value and title"""
    def __init__(self, title="Metric", value="0", accent_color=None, **kwargs):
        kwargs["orientation"] = "vertical"
        kwargs["padding"] = [dp(14), dp(12)]
        kwargs["spacing"] = dp(4)
        super().__init__(**kwargs)
        accent = accent_color or COLORS["primary"]

        self.val_label = Label(
            text=str(value),
            font_size="24sp",
            bold=True,
            color=accent,
            halign="left",
            valign="middle",
            size_hint_y=0.65
        )
        self.val_label.bind(size=self.val_label.setter("text_size"))

        self.title_label = Label(
            text=title,
            font_size="12sp",
            color=COLORS["text_muted"],
            halign="left",
            valign="middle",
            size_hint_y=0.35
        )
        self.title_label.bind(size=self.title_label.setter("text_size"))

        self.add_widget(self.val_label)
        self.add_widget(self.title_label)

    def update_value(self, val):
        self.val_label.text = str(val)

class CyberButton(Button):
    """Button with customizable color palette and clean style"""
    def __init__(self, btn_type="primary", radius=6, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0) # transparent default
        self.btn_type = btn_type
        self.radius = radius
        self.color = COLORS["text_main"]
        self.bold = True
        self.font_size = "13sp"

        if btn_type == "primary":
            self.base_color = COLORS["primary"]
        elif btn_type == "danger":
            self.base_color = COLORS["danger"]
        elif btn_type == "warning":
            self.base_color = COLORS["warning"]
        elif btn_type == "info":
            self.base_color = COLORS["info"]
        elif btn_type == "secondary":
            self.base_color = COLORS["card_hover"]
        else:
            self.base_color = COLORS["card_hover"]

        self.bind(pos=self._redraw, size=self._redraw, state=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == "down":
                Color(self.base_color[0] * 0.8, self.base_color[1] * 0.8, self.base_color[2] * 0.8, 1.0)
            else:
                Color(*self.base_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius)])

class CyberInput(TextInput):
    """Dark-themed text input with padding and subtle border"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = COLORS["text_main"]
        self.cursor_color = COLORS["primary"]
        self.padding = [dp(12), dp(10)]
        self.font_size = "14sp"
        self.bind(pos=self._update_canvas, size=self._update_canvas, focus=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS["input_bg"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            if self.focus:
                Color(*COLORS["primary"])
                Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(6)], width=1.5)
            else:
                Color(*COLORS["input_border"])
                Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(6)], width=1.0)

class StatusBadge(Label):
    """Pill badge showing status with color code"""
    def __init__(self, text="UNKNOWN", badge_type="danger", **kwargs):
        super().__init__(**kwargs)
        self.font_size = "11sp"
        self.bold = True
        self.text = f" {text} "
        self.badge_type = badge_type
        self.color = COLORS["text_main"]
        self.size_hint = (None, None)
        self.size = (dp(85), dp(24))

        if badge_type == "success" or text == "KNOWN" or text == "active":
            self.bg_color = (0.063, 0.725, 0.506, 0.85)
        elif badge_type == "danger" or text == "UNKNOWN" or text == "CRITICAL":
            self.bg_color = (0.937, 0.267, 0.267, 0.85)
        elif badge_type == "warning" or text == "ENTRY" or text == "EXIT":
            self.bg_color = (0.961, 0.620, 0.043, 0.85)
        elif badge_type == "info" or text == "PERSON" or text == "VEHICLE":
            self.bg_color = (0.231, 0.510, 0.965, 0.85)
        else:
            self.bg_color = (0.2, 0.25, 0.35, 0.85)

        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
