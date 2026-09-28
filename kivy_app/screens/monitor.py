"""
AEGIS AI - Live Surveillance Monitor Screen
Real-time OpenCV/YOLO video feed rendering onto Kivy Texture
"""
import time
import cv2
import numpy as np
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, CyberButton, StatusBadge, COLORS
from services.camera_service import camera_service
from services.storage_service import storage_service
from models import db, Event, Camera

class MonitorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clock_event = None
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="horizontal", spacing=dp(16), padding=dp(16))

        # LEFT / MAIN: Video Viewport & Controls
        left_box = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_x=0.72)

        # Video Frame Container
        self.video_card = CyberCard(orientation="vertical", padding=dp(6), radius=8)
        self.camera_image = Image(
            fit_mode="contain",
            size_hint=(1, 1)
        )
        self.video_card.add_widget(self.camera_image)
        left_box.add_widget(self.video_card)

        # Bottom Controls Toolbar
        controls_card = CyberCard(
            orientation="horizontal",
            spacing=dp(10),
            padding=[dp(12), dp(10)],
            size_hint_y=None,
            height=dp(56),
            radius=8
        )

        self.btn_toggle_run = CyberButton(
            text="START STREAM",
            btn_type="primary",
            size_hint_x=0.22,
            on_release=self.toggle_monitoring
        )

        self.btn_pause = CyberButton(
            text="PAUSE",
            btn_type="warning",
            size_hint_x=0.18,
            on_release=self.toggle_pause
        )

        self.btn_snapshot = CyberButton(
            text="CAPTURE SNAPSHOT",
            btn_type="info",
            size_hint_x=0.25,
            on_release=self.take_snapshot
        )

        self.status_feedback = Label(
            text="Ready",
            font_size="12sp",
            color=COLORS["text_muted"],
            halign="left",
            size_hint_x=0.35
        )
        self.status_feedback.bind(size=self.status_feedback.setter("text_size"))

        controls_card.add_widget(self.btn_toggle_run)
        controls_card.add_widget(self.btn_pause)
        controls_card.add_widget(self.btn_snapshot)
        controls_card.add_widget(self.status_feedback)

        left_box.add_widget(controls_card)
        root.add_widget(left_box)

        # RIGHT: Real-Time Telemetry & Target Detections
        right_box = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_x=0.28)

        # Telemetry Card
        telemetry_card = CyberCard(
            orientation="vertical",
            padding=[dp(14), dp(12)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(170),
            radius=8
        )
        t_title = Label(
            text="[b]CAMERA TELEMETRY[/b]",
            markup=True,
            font_size="13sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(20),
            halign="left"
        )
        t_title.bind(size=t_title.setter("text_size"))
        telemetry_card.add_widget(t_title)

        self.lbl_cam_name = Label(text="Camera: Main Entrance", font_size="12sp", color=COLORS["text_main"], size_hint_y=None, height=dp(20), halign="left")
        self.lbl_cam_name.bind(size=self.lbl_cam_name.setter("text_size"))
        self.lbl_cam_source = Label(text="Source: Default (0)", font_size="12sp", color=COLORS["text_muted"], size_hint_y=None, height=dp(20), halign="left")
        self.lbl_cam_source.bind(size=self.lbl_cam_source.setter("text_size"))
        self.lbl_fps = Label(text="Render Rate: 0.0 FPS", font_size="12sp", color=COLORS["info"], size_hint_y=None, height=dp(20), halign="left")
        self.lbl_fps.bind(size=self.lbl_fps.setter("text_size"))
        self.lbl_status = Label(text="Status: OFFLINE", font_size="12sp", color=COLORS["danger"], size_hint_y=None, height=dp(20), halign="left")
        self.lbl_status.bind(size=self.lbl_status.setter("text_size"))

        telemetry_card.add_widget(self.lbl_cam_name)
        telemetry_card.add_widget(self.lbl_cam_source)
        telemetry_card.add_widget(self.lbl_fps)
        telemetry_card.add_widget(self.lbl_status)
        right_box.add_widget(telemetry_card)

        # Target Detections Card
        targets_card = CyberCard(
            orientation="vertical",
            padding=[dp(14), dp(12)],
            spacing=dp(8),
            radius=8
        )
        tgt_title = Label(
            text="[b]ACTIVE DETECTIONS & TRACKS[/b]",
            markup=True,
            font_size="13sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(22),
            halign="left"
        )
        tgt_title.bind(size=tgt_title.setter("text_size"))
        targets_card.add_widget(tgt_title)

        self.targets_scroll = ScrollView(size_hint=(1, 1))
        self.targets_layout = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.targets_layout.bind(minimum_height=self.targets_layout.setter("height"))
        self.targets_scroll.add_widget(self.targets_layout)
        targets_card.add_widget(self.targets_scroll)

        right_box.add_widget(targets_card)
        root.add_widget(right_box)

        self.add_widget(root)

    def on_enter(self):
        """Called when this screen is navigated to"""
        self.update_controls_state()
        if self.clock_event is None:
            # 30 FPS update loop for live texture render
            self.clock_event = Clock.schedule_interval(self.update_live_feed, 1.0 / 30.0)

    def on_leave(self):
        """Called when user navigates away from this screen"""
        if self.clock_event is not None:
            self.clock_event.cancel()
            self.clock_event = None

    def update_controls_state(self):
        is_running = camera_service.is_running
        is_paused = camera_service.is_paused

        if is_running:
            self.btn_toggle_run.text = "STOP STREAM"
            self.btn_toggle_run.base_color = COLORS["danger"]
        else:
            self.btn_toggle_run.text = "START STREAM"
            self.btn_toggle_run.base_color = COLORS["primary"]

        if is_paused:
            self.btn_pause.text = "RESUME"
            self.btn_pause.base_color = COLORS["primary"]
        else:
            self.btn_pause.text = "PAUSE"
            self.btn_pause.base_color = COLORS["warning"]

        self.btn_toggle_run._redraw()
        self.btn_pause._redraw()

    def toggle_monitoring(self, *args):
        if camera_service.is_running:
            camera_service.stop_monitoring()
            self.status_feedback.text = "Stream stopped."
        else:
            from kivy.app import App
            app = App.get_running_app()
            camera_service.init_app(app.flask_app)
            camera_service.start_monitoring()
            self.status_feedback.text = "Stream starting..."
        self.update_controls_state()

    def toggle_pause(self, *args):
        if not camera_service.is_running:
            return
        if camera_service.is_paused:
            camera_service.resume_monitoring()
            self.status_feedback.text = "Monitoring resumed."
        else:
            camera_service.pause_monitoring()
            self.status_feedback.text = "Monitoring paused."
        self.update_controls_state()

    def take_snapshot(self, *args):
        raw_frame = camera_service.get_latest_frame(processed=False)
        if raw_frame is None or raw_frame.size == 0:
            self.status_feedback.text = "No frame available to snapshot."
            return

        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                rel_path = storage_service.save_snapshot(raw_frame, prefix="kivy_manual")
                ev = Event(
                    camera_id=camera_service.camera_id,
                    entity_type="MANUAL_SNAPSHOT",
                    entity_name="Manual Snapshot",
                    recognition_status="NOT_APPLICABLE",
                    event_type="MANUAL",
                    direction="NONE",
                    confidence=1.0,
                    snapshot_path=rel_path
                )
                db.session.add(ev)
                db.session.commit()
                self.status_feedback.text = f"Snapshot saved: #{ev.id}"
        except Exception as e:
            self.status_feedback.text = f"Snapshot error: {e}"

    def update_live_feed(self, dt):
        frame = camera_service.get_latest_frame(processed=True)
        if frame is None or frame.size == 0:
            return

        # Frame is BGR numpy array from OpenCV
        # Flip vertically for Kivy OpenGL coordinates
        buf = cv2.flip(frame, 0).tobytes()
        h, w = frame.shape[:2]

        texture = Texture.create(size=(w, h), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.camera_image.texture = texture

        # Update Telemetry Display
        status_info = camera_service.get_status()
        self.lbl_cam_name.text = f"Camera: {status_info.get('camera_name', 'Main Entrance')}"
        self.lbl_cam_source.text = f"Source: {status_info.get('source', '0')} {'(Synthetic)' if status_info.get('synthetic') else ''}"
        self.lbl_fps.text = f"Render Rate: {status_info.get('fps', 0):.1f} FPS"
        
        status_str = status_info.get("status", "OFFLINE")
        if status_str == "LIVE":
            self.lbl_status.color = COLORS["primary"]
        elif status_str == "PAUSED":
            self.lbl_status.color = COLORS["warning"]
        else:
            self.lbl_status.color = COLORS["danger"]
        self.lbl_status.text = f"Status: {status_str}"

        # Update Active Detections list
        tracks = camera_service.active_tracks or []
        self.targets_layout.clear_widgets()

        if not tracks:
            empty_lbl = Label(
                text="No active targets in view",
                font_size="12sp",
                color=COLORS["text_muted"],
                size_hint_y=None,
                height=dp(28)
            )
            self.targets_layout.add_widget(empty_lbl)
        else:
            for t in tracks:
                row = CyberCard(
                    orientation="horizontal",
                    padding=[dp(8), dp(6)],
                    spacing=dp(6),
                    size_hint_y=None,
                    height=dp(36),
                    bg_color=COLORS["card_hover"],
                    radius=4
                )
                name = t.get("person_name") or t.get("class_name", "Object")
                rec = t.get("recognition_status", "N/A")
                conf = int(t.get("confidence", 0) * 100)
                dir_crossed = t.get("direction", "NONE")

                lbl = Label(
                    text=f"[b]{name}[/b] ({conf}%)",
                    markup=True,
                    font_size="11sp",
                    color=COLORS["text_main"],
                    halign="left",
                    size_hint_x=0.55
                )
                lbl.bind(size=lbl.setter("text_size"))
                row.add_widget(lbl)

                badge = StatusBadge(text=rec if rec != "NOT_APPLICABLE" else dir_crossed, size_hint_x=0.45)
                row.add_widget(badge)
                self.targets_layout.add_widget(row)
