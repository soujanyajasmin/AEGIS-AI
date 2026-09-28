"""
AEGIS AI - Global System Thresholds & Parameters Configuration Screen
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, CyberButton, CyberInput, COLORS
from models import db, SystemSetting
from config import Config
from services.camera_service import camera_service

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))

        top = BoxLayout(size_hint_y=None, height=dp(38))
        lbl = Label(text="[b]SYSTEM THRESHOLDS & INFERENCE PARAMETERS[/b]", markup=True, font_size="16sp", color=COLORS["text_main"], halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        top.add_widget(lbl)
        root.add_widget(top)

        card = CyberCard(orientation="vertical", padding=[dp(20), dp(16)], spacing=dp(14), size_hint_y=1, radius=8)
        f_grid = GridLayout(cols=2, spacing=dp(14), size_hint_y=0.7)

        # 1. Detection Confidence
        f_grid.add_widget(Label(text="YOLO Detection Confidence (0.1 - 0.95)", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_conf = CyberInput(multiline=False, text=str(Config.DETECTION_CONFIDENCE))
        f_grid.add_widget(self.in_conf)

        # 2. Face Recognition Threshold
        f_grid.add_widget(Label(text="Face Cosine Similarity Threshold (0.2 - 0.8)", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_face = CyberInput(multiline=False, text=str(Config.FACE_RECOGNITION_THRESHOLD))
        f_grid.add_widget(self.in_face)

        # 3. Event Cooldown
        f_grid.add_widget(Label(text="Event Cooldown Period (Seconds)", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_cooldown = CyberInput(multiline=False, text=str(Config.EVENT_COOLDOWN))
        f_grid.add_widget(self.in_cooldown)

        # 4. Retention Days
        f_grid.add_widget(Label(text="Automated Retention Lifespan (Days)", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_retention = CyberInput(multiline=False, text=str(Config.RETENTION_DAYS))
        f_grid.add_widget(self.in_retention)

        # 5. Frame Skip
        f_grid.add_widget(Label(text="Inference Frame Skip (1 = Every frame)", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_skip = CyberInput(multiline=False, text=str(Config.FRAME_SKIP))
        f_grid.add_widget(self.in_skip)

        card.add_widget(f_grid)

        self.lbl_feedback = Label(text="", font_size="12sp", color=COLORS["primary"], size_hint_y=None, height=dp(24), halign="left")
        self.lbl_feedback.bind(size=self.lbl_feedback.setter("text_size"))
        card.add_widget(self.lbl_feedback)

        btn_save = CyberButton(text="SAVE SYSTEM SETTINGS", btn_type="primary", size_hint_y=None, height=dp(46), on_release=self.save_settings)
        card.add_widget(btn_save)

        # Spacer
        card.add_widget(Label(size_hint_y=1))

        root.add_widget(card)
        self.add_widget(root)

    def on_enter(self):
        self.load_settings()

    def load_settings(self):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                self.in_conf.text = str(SystemSetting.get("DETECTION_CONFIDENCE", Config.DETECTION_CONFIDENCE))
                self.in_face.text = str(SystemSetting.get("FACE_RECOGNITION_THRESHOLD", Config.FACE_RECOGNITION_THRESHOLD))
                self.in_cooldown.text = str(SystemSetting.get("EVENT_COOLDOWN", Config.EVENT_COOLDOWN))
                self.in_retention.text = str(SystemSetting.get("RETENTION_DAYS", Config.RETENTION_DAYS))
                self.in_skip.text = str(SystemSetting.get("FRAME_SKIP", Config.FRAME_SKIP))
        except Exception as e:
            print(f"[SettingsScreen] Error loading settings: {e}")

    def save_settings(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                SystemSetting.set("DETECTION_CONFIDENCE", self.in_conf.text.strip(), "YOLO detection confidence")
                SystemSetting.set("FACE_RECOGNITION_THRESHOLD", self.in_face.text.strip(), "Face match threshold")
                SystemSetting.set("EVENT_COOLDOWN", self.in_cooldown.text.strip(), "Event cooldown in seconds")
                SystemSetting.set("RETENTION_DAYS", self.in_retention.text.strip(), "Data retention lifespan in days")
                SystemSetting.set("FRAME_SKIP", self.in_skip.text.strip(), "Frame skip factor")

                # Apply immediately to camera service
                camera_service.conf_threshold = float(self.in_conf.text.strip())
                camera_service.frame_skip = int(self.in_skip.text.strip())

                self.lbl_feedback.color = COLORS["primary"]
                self.lbl_feedback.text = "System settings updated and applied successfully."
        except Exception as e:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = f"Error saving settings: {e}"
