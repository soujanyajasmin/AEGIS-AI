"""
AEGIS AI - Biometric Face Enrollment Screen
Extracts YuNet + SFace embeddings directly from live camera feed or local image file
"""
from pathlib import Path
import cv2
import numpy as np

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.metrics import dp

from kivy_app.ui_components import CyberCard, CyberButton, CyberInput, StatusBadge, COLORS
from models import db, Person, FaceEmbedding
from services.camera_service import camera_service
from services.face_recognition_service import face_recognition_service
from services.storage_service import storage_service

class EnrollmentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.person_map = {} # label -> id
        self.preview_frame = None
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="horizontal", spacing=dp(16), padding=dp(16))

        # LEFT (50%): Face Capture & Viewport
        left_card = CyberCard(orientation="vertical", padding=dp(14), spacing=dp(10), size_hint_x=0.52)
        lbl_l = Label(
            text="[b]BIOMETRIC CAPTURE & VALIDATION[/b]",
            markup=True,
            font_size="14sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        lbl_l.bind(size=lbl_l.setter("text_size"))
        left_card.add_widget(lbl_l)

        # Image preview
        self.img_preview = Image(fit_mode="contain", size_hint_y=0.75)
        left_card.add_widget(self.img_preview)

        # Buttons to grab from camera or file
        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(44))
        btn_grab = CyberButton(text="GRAB FROM CAMERA", btn_type="info", size_hint_x=0.5, on_release=self.grab_from_camera)
        btn_load = CyberButton(text="LOAD FROM FILE", btn_type="secondary", size_hint_x=0.5, on_release=self.load_from_path)
        btn_row.add_widget(btn_grab)
        btn_row.add_widget(btn_load)
        left_card.add_widget(btn_row)

        root.add_widget(left_card)

        # RIGHT (50%): Subject Selection & Enrollment Controls
        right_card = CyberCard(orientation="vertical", padding=dp(16), spacing=dp(14), size_hint_x=0.48)
        lbl_r = Label(
            text="[b]SUBJECT ASSIGNMENT & ENROLLMENT[/b]",
            markup=True,
            font_size="14sp",
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        lbl_r.bind(size=lbl_r.setter("text_size"))
        right_card.add_widget(lbl_r)

        # Subject Selector
        s_lbl = Label(text="Select Subject to Enroll:", font_size="12sp", color=COLORS["text_muted"], halign="left", size_hint_y=None, height=dp(18))
        s_lbl.bind(size=s_lbl.setter("text_size"))
        right_card.add_widget(s_lbl)

        self.spin_person = Spinner(
            text="-- Choose Subject --",
            values=["-- Choose Subject --"],
            size_hint_y=None,
            height=dp(42),
            background_color=COLORS["input_bg"],
            color=COLORS["text_main"]
        )
        right_card.add_widget(self.spin_person)

        # File path input (optional alternative to grab)
        f_lbl = Label(text="Or Image File Path:", font_size="12sp", color=COLORS["text_muted"], halign="left", size_hint_y=None, height=dp(18))
        f_lbl.bind(size=f_lbl.setter("text_size"))
        right_card.add_widget(f_lbl)

        self.in_file_path = CyberInput(multiline=False, size_hint_y=None, height=dp(42), hint_text="C:/path/to/face.jpg")
        right_card.add_widget(self.in_file_path)

        # Enrollment Process Button
        self.btn_enroll = CyberButton(
            text="ANALYZE & ENROLL FACE",
            btn_type="primary",
            size_hint_y=None,
            height=dp(46),
            on_release=self.process_enrollment
        )
        right_card.add_widget(self.btn_enroll)

        # Feedback & Quality Score
        self.lbl_feedback = Label(
            text="Ready to capture.",
            font_size="12sp",
            color=COLORS["text_muted"],
            halign="left",
            size_hint_y=None,
            height=dp(60)
        )
        self.lbl_feedback.bind(size=self.lbl_feedback.setter("text_size"))
        right_card.add_widget(self.lbl_feedback)

        # Database retrain button
        btn_retrain = CyberButton(
            text="RE-TRAIN RECOGNITION CACHE",
            btn_type="warning",
            size_hint_y=None,
            height=dp(40),
            on_release=self.retrain_cache
        )
        right_card.add_widget(btn_retrain)

        # Spacer
        right_card.add_widget(Label(size_hint_y=1))

        root.add_widget(right_card)
        self.add_widget(root)

    def on_enter(self):
        self.load_persons_dropdown()

    def load_persons_dropdown(self):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                persons = Person.query.filter_by(status="active").all()
                self.person_map = {f"{p.name} (#{p.id})": p.id for p in persons}
                if self.person_map:
                    self.spin_person.values = list(self.person_map.keys())
                    self.spin_person.text = list(self.person_map.keys())[0]
                else:
                    self.spin_person.values = ["No active subjects found"]
                    self.spin_person.text = "No active subjects found"
        except Exception as e:
            print(f"[EnrollmentScreen] Dropdown error: {e}")

    def grab_from_camera(self, *args):
        frame = camera_service.get_latest_frame(processed=False)
        if frame is None or frame.size == 0:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = "Cannot grab: Camera stream is not active or providing frames."
            return

        self.preview_frame = frame.copy()
        self._display_frame(self.preview_frame)
        self.lbl_feedback.color = COLORS["info"]
        self.lbl_feedback.text = "Captured fresh frame from live stream. Ready to analyze."

    def load_from_path(self, *args):
        path_str = self.in_file_path.text.strip().strip('"').strip("'")
        if not path_str or not Path(path_str).exists():
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = "Specified file does not exist on disk."
            return

        frame = cv2.imread(path_str)
        if frame is None:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = "Failed to decode image file."
            return

        self.preview_frame = frame
        self._display_frame(self.preview_frame)
        self.lbl_feedback.color = COLORS["info"]
        self.lbl_feedback.text = f"Loaded image from {Path(path_str).name}."

    def _display_frame(self, frame):
        buf = cv2.flip(frame, 0).tobytes()
        h, w = frame.shape[:2]
        texture = Texture.create(size=(w, h), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img_preview.texture = texture

    def process_enrollment(self, *args):
        if self.preview_frame is None:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = "Please grab a camera frame or load an image first."
            return

        selected_label = self.spin_person.text
        person_id = self.person_map.get(selected_label)
        if not person_id:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = "Please select a valid subject."
            return

        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                person = Person.query.get(person_id)
                if not person:
                    self.lbl_feedback.text = "Person record not found."
                    return

                # 1. Detect faces using YuNet
                faces = face_recognition_service.detect_faces(self.preview_frame, score_threshold=0.5)
                if not faces:
                    self.lbl_feedback.color = COLORS["danger"]
                    self.lbl_feedback.text = "No face detected in image. Ensure face is centered with clear lighting."
                    return

                if len(faces) > 1:
                    self.lbl_feedback.color = COLORS["warning"]
                    self.lbl_feedback.text = f"Multiple faces ({len(faces)}) detected. Please ensure only 1 person in frame."
                    return

                best_face = faces[0]

                # 2. Validate quality
                is_valid, reason, quality = face_recognition_service.validate_face_quality(self.preview_frame, best_face)
                if not is_valid:
                    self.lbl_feedback.color = COLORS["danger"]
                    self.lbl_feedback.text = f"Quality check failed: {reason}"
                    return

                # 3. Crop face sample
                x, y, w, h = best_face[0:4].astype(int)
                img_h, img_w = self.preview_frame.shape[:2]
                pad_x, pad_y = int(w * 0.2), int(h * 0.2)
                x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
                x2, y2 = min(img_w, x + w + pad_x), min(img_h, y + h + pad_y)
                face_crop = self.preview_frame[y1:y2, x1:x2]

                sample_path = storage_service.save_face_sample(face_crop if face_crop.size > 0 else self.preview_frame, person.id)

                # 4. Enroll sample into DB & memory cache
                success, msg, emb_id = face_recognition_service.enroll_person_sample(person.id, self.preview_frame, best_face, sample_path)
                if success:
                    self.lbl_feedback.color = COLORS["primary"]
                    self.lbl_feedback.text = f"Successfully enrolled! Quality score: {quality:.2f}. Total samples: {person.embeddings.count()}."
                else:
                    self.lbl_feedback.color = COLORS["danger"]
                    self.lbl_feedback.text = f"Enrollment error: {msg}"

        except Exception as e:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = f"Error during enrollment: {e}"

    def retrain_cache(self, *args):
        from kivy.app import App
        app = App.get_running_app()
        try:
            with app.flask_app.app_context():
                face_recognition_service.train_database()
                count = len(face_recognition_service.known_faces_cache)
                self.lbl_feedback.color = COLORS["primary"]
                self.lbl_feedback.text = f"Database re-trained. {count} active face subjects in fast memory cache."
        except Exception as e:
            self.lbl_feedback.color = COLORS["danger"]
            self.lbl_feedback.text = f"Error reloading database: {e}"
