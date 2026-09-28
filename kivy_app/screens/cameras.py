"""
AEGIS AI - Camera Management & Boundary Configuration Screen
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, CyberButton, CyberInput, COLORS
from models import db, Camera
from services.camera_service import camera_service

class CamerasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_obj = None
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))

        # Header
        top = BoxLayout(size_hint_y=None, height=dp(38))
        lbl = Label(text="[b]CAMERA HARDWARE & BOUNDARY TRIPWIRE CONFIGURATION[/b]", markup=True, font_size="16sp", color=COLORS["text_main"], halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        top.add_widget(lbl)
        root.add_widget(top)

        # Main Card
        card = CyberCard(orientation="vertical", padding=[dp(20), dp(16)], spacing=dp(14), size_hint_y=1, radius=8)

        # Form Grid
        f_grid = GridLayout(cols=2, spacing=dp(14), size_hint_y=0.75)

        # 1. Camera Name
        f_grid.add_widget(Label(text="Camera Name", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_name = CyberInput(multiline=False, text="Main Entrance (Camera #1)")
        f_grid.add_widget(self.in_name)

        # 2. Camera Source
        f_grid.add_widget(Label(text="Source (0, 1, RTSP URL, or file)", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.in_source = CyberInput(multiline=False, text="0")
        f_grid.add_widget(self.in_source)

        # 3. Source Type
        f_grid.add_widget(Label(text="Source Type", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.spin_type = Spinner(
            text="webcam",
            values=["webcam", "rtsp", "video"],
            background_color=COLORS["input_bg"],
            color=COLORS["text_main"]
        )
        f_grid.add_widget(self.spin_type)

        # 4. Detection Confidence Slider
        self.lbl_conf = Label(text="Detection Confidence Threshold (45%)", font_size="13sp", color=COLORS["text_muted"], halign="left")
        f_grid.add_widget(self.lbl_conf)
        self.slider_conf = Slider(min=0.10, max=0.95, value=0.45, step=0.05)
        self.slider_conf.bind(value=self.on_conf_change)
        f_grid.add_widget(self.slider_conf)

        # 5. Face Recognition Threshold Slider
        self.lbl_face = Label(text="Face Match Threshold (40%)", font_size="13sp", color=COLORS["text_muted"], halign="left")
        f_grid.add_widget(self.lbl_face)
        self.slider_face = Slider(min=0.20, max=0.80, value=0.40, step=0.05)
        self.slider_face.bind(value=self.on_face_change)
        f_grid.add_widget(self.slider_face)

        # 6. Virtual Line Orientation
        f_grid.add_widget(Label(text="Boundary Tripwire Orientation", font_size="13sp", color=COLORS["text_muted"], halign="left"))
        self.spin_orient = Spinner(
            text="horizontal",
            values=["horizontal", "vertical"],
            background_color=COLORS["input_bg"],
            color=COLORS["text_main"]
        )
        f_grid.add_widget(self.spin_orient)

        # 7. Virtual Line Position Slider
        self.lbl_pos = Label(text="Boundary Line Position (50%)", font_size="13sp", color=COLORS["text_muted"], halign="left")
        f_grid.add_widget(self.lbl_pos)
        self.slider_pos = Slider(min=0.10, max=0.90, value=0.50, step=0.05)
        self.slider_pos.bind(value=self.on_pos_change)
        f_grid.add_widget(self.slider_pos)

        card.add_widget(f_grid)

        # Feedback message
        self.lbl_feedback = Label(text="", font_size="12sp", color=COLORS["primary"], size_hint_y=None, height=dp(24), halign="left")
        self.lbl_feedback.bind(size=self.lbl_feedback.setter("text_size"))
        card.add_widget(self.lbl_feedback)

        # Action Buttons
        btn_box = BoxLayout(spacing=dp(12), size_hint_y=None, height=dp(46))
        btn_save = CyberButton(text="SAVE & APPLY CONFIGURATION", btn_type="primary", size_hint_x=0.5, on_release=self.save_and_apply)
        btn_reconnect = CyberButton(text="FORCE RE-CONNECT", btn_type="warning", size_hint_x=0.5, on_release=self.reconnect_stream)
        btn_box.add_widget(btn_save)
        btn_box.add_widget(btn_reconnect)
        card.add_widget(btn_box)

        root.add_widget(card)
        self.add_widget(root)

    def on_conf_change(self, instance, val):
        self.lbl_conf.text = f"Detection Confidence Threshold ({int(val*100)}%)"

    def on_face_change(self, instance, val):
        self.lbl_face.text = f"Face Match Threshold ({int(val*100)}%)"

    def on_pos_change(self, instance, val):
        self.lbl_pos.text = f"Boundary Line Position ({int(val*100)}%)"

    def on_enter(self):
        self.load_camera_config()

    def load_camera_config(self):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                cam = Camera.query.first()
                if cam:
                    self.camera_obj = cam
                    self.in_name.text = cam.name
                    self.in_source.text = str(cam.source)
                    self.spin_type.text = cam.source_type
                    self.slider_conf.value = cam.confidence_threshold
                    self.slider_face.value = cam.face_threshold
                    self.spin_orient.text = cam.line_orientation
                    self.slider_pos.value = cam.line_position
        except Exception as e:
            print(f"[CamerasScreen] Error loading camera: {e}")

    def save_and_apply(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                cam = Camera.query.first()
                if not cam:
                    cam = Camera(name=self.in_name.text.strip(), source=self.in_source.text.strip())
                    db.session.add(cam)

                cam.name = self.in_name.text.strip()
                cam.source = self.in_source.text.strip()
                cam.source_type = self.spin_type.text
                cam.confidence_threshold = float(self.slider_conf.value)
                cam.face_threshold = float(self.slider_face.value)
                cam.line_orientation = self.spin_orient.text
                cam.line_position = float(self.slider_pos.value)
                db.session.commit()

                # Reconfigure camera service immediately
                camera_service.configure_from_camera(cam)
                self.lbl_feedback.color = COLORS["primary"]
                self.lbl_feedback.text = "Camera configuration saved and active parameters applied to live stream."
        except Exception as e:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = f"Error saving camera config: {e}"

    def reconnect_stream(self, *args):
        was_running = camera_service.is_running
        camera_service.stop_monitoring()
        if was_running:
            from kivy.app import App
            app = App.get_running_app()
            camera_service.init_app(app.flask_app)
            camera_service.start_monitoring()
        self.lbl_feedback.color = COLORS["info"]
        self.lbl_feedback.text = "Camera stream reconnected."
