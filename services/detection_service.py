import os
import threading
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from config import Config
from services.face_recognition_service import face_recognition_service

class DetectionService:
    # Mappings from COCO classes to our high-level premise security categories
    PERSON_CLASSES = {"person"}
    VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle", "airplane", "boat", "train"}
    ANIMAL_CLASSES = {"dog", "cat", "bird", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}

    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model_name = model_name
        self.model = None
        self.lock = threading.Lock()
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        """Loads YOLO model once during startup"""
        with self.lock:
            try:
                models_dir = Path(Config.MODELS_DIR)
                local_path = models_dir / self.model_name
                target = str(local_path) if local_path.exists() else self.model_name

                print(f"[DetectionService] Loading YOLO model from {target}...")
                self.model = YOLO(target)
                self.is_loaded = True
                print("[DetectionService] YOLO model loaded successfully.")
            except Exception as e:
                print(f"[DetectionService] Error loading YOLO model: {e}")
                self.is_loaded = False

    def categorize_class(self, class_name: str) -> str:
        name_lower = class_name.lower()
        if name_lower in self.PERSON_CLASSES:
            return "PERSON"
        elif name_lower in self.VEHICLE_CLASSES:
            return "VEHICLE"
        elif name_lower in self.ANIMAL_CLASSES:
            return "ANIMAL"
        return "OTHER"

    def detect_objects(self, frame: np.ndarray, conf_threshold: float = 0.45) -> List[dict]:
        """
        Runs YOLO object detection on the frame.
        For every detected person, runs face detection and recognition.
        Returns a list of structured detections.
        """
        if not self.is_loaded or self.model is None or frame is None:
            return []

        h, w = frame.shape[:2]
        detections = []

        with self.lock:
            try:
                # Fast inference, non-verbose
                results = self.model.predict(
                    source=frame,
                    conf=conf_threshold,
                    verbose=False,
                    imgsz=640
                )
            except Exception as e:
                print(f"[DetectionService] Prediction error: {e}")
                return []

        if not results or len(results) == 0:
            return []

        r = results[0]
        boxes = r.boxes

        if boxes is None or len(boxes) == 0:
            return []

        for box in boxes:
            cls_id = int(box.cls[0].item())
            class_name = self.model.names.get(cls_id, f"class_{cls_id}")
            confidence = float(box.conf[0].item())
            coords = box.xyxy[0].tolist() # [x1, y1, x2, y2]
            x1, y1, x2, y2 = [int(v) for v in coords]

            # Clip to frame dimensions
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(x1 + 1, min(w, x2))
            y2 = max(y1 + 1, min(h, y2))

            entity_type = self.categorize_class(class_name)
            det_info = {
                "bbox": [x1, y1, x2, y2],
                "class_name": class_name,
                "entity_type": entity_type,
                "confidence": confidence,
                "recognition_status": "NOT_APPLICABLE",
                "person_name": None,
                "person_id": None
            }

            # If person detected, perform Face Detection & Recognition
            if entity_type == "PERSON":
                person_crop = frame[y1:y2, x1:x2]
                det_info["recognition_status"] = "UNKNOWN"
                det_info["person_name"] = "Unknown Person"

                if person_crop.size > 0:
                    faces = face_recognition_service.detect_faces(person_crop, score_threshold=0.5)
                    if faces:
                        # Pick best/largest face
                        best_face = faces[0]
                        # Recognize face
                        pid, pname, score, status = face_recognition_service.recognize_face(person_crop, best_face)
                        det_info["recognition_status"] = status
                        det_info["person_name"] = pname
                        det_info["person_id"] = pid
                        det_info["face_score"] = score

            detections.append(det_info)

        return detections

    def draw_overlays(
        self,
        frame: np.ndarray,
        tracks: List[dict],
        line_pos: float = 0.50,
        line_orientation: str = "horizontal",
        fps: float = 0.0,
        camera_name: str = "Camera #1"
    ) -> np.ndarray:
        """
        Draws visual overlays on the frame:
        - Modern cyber-security HUD header
        - Entry/Exit virtual boundary line with directional arrows
        - Color-coded bounding boxes according to entity & recognition status
        - Labels with icons, confidence, and tracking IDs
        """
        if frame is None:
            return frame

        overlay = frame.copy()
        h, w = frame.shape[:2]

        # 1. Draw Virtual Line
        line_color = (0, 220, 255) # Bright Cyan/Yellow
        if line_orientation == "horizontal":
            line_y = int(h * line_pos)
            cv2.line(overlay, (0, line_y), (w, line_y), line_color, 2, cv2.LINE_AA)
            cv2.putText(overlay, "ENTRY / EXIT LINE [TOP: EXIT | BOTTOM: ENTRY]", (15, line_y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, line_color, 1, cv2.LINE_AA)
        else:
            line_x = int(w * line_pos)
            cv2.line(overlay, (line_x, 0), (line_x, h), line_color, 2, cv2.LINE_AA)
            cv2.putText(overlay, "ENTRY / EXIT LINE", (line_x + 8, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, line_color, 1, cv2.LINE_AA)

        # 2. Draw Object Tracks & Bounding Boxes
        for track in tracks:
            bbox = track["bbox"]
            x1, y1, x2, y2 = bbox
            entity_type = track["entity_type"]
            rec_status = track.get("recognition_status", "NOT_APPLICABLE")
            person_name = track.get("person_name")
            obj_id = track.get("object_id", "?")
            confidence = track.get("confidence", 0.0)
            direction = track.get("direction", "NONE")

            # Determine color scheme (BGR)
            if entity_type == "PERSON":
                if rec_status == "KNOWN":
                    box_color = (16, 185, 129) # Emerald Green (BGR: 129, 185, 16)
                    label_text = f"KNOWN: {person_name} #{obj_id}"
                else:
                    box_color = (68, 68, 239) # Bright Crimson Red
                    label_text = f"UNKNOWN PERSON #{obj_id}"
            elif entity_type == "VEHICLE":
                box_color = (246, 130, 59) # Electric Blue
                label_text = f"VEHICLE: {track['class_name'].upper()} #{obj_id}"
            elif entity_type == "ANIMAL":
                box_color = (11, 158, 245) # Amber Orange
                label_text = f"ANIMAL: {track['class_name'].upper()} #{obj_id}"
            else:
                box_color = (247, 85, 168) # Purple
                label_text = f"{track['class_name'].upper()} #{obj_id}"

            if direction != "NONE":
                label_text += f" [{direction}]"

            # Draw rounded/corner-accented bounding box
            cv2.rectangle(overlay, (x1, y1), (x2, y2), box_color, 2, cv2.LINE_AA)

            # Draw corner accents
            corner_len = min(20, int((x2 - x1) / 4), int((y2 - y1) / 4))
            thick = 3
            # Top-left
            cv2.line(overlay, (x1, y1), (x1 + corner_len, y1), box_color, thick)
            cv2.line(overlay, (x1, y1), (x1, y1 + corner_len), box_color, thick)
            # Top-right
            cv2.line(overlay, (x2, y1), (x2 - corner_len, y1), box_color, thick)
            cv2.line(overlay, (x2, y1), (x2, y1 + corner_len), box_color, thick)
            # Bottom-left
            cv2.line(overlay, (x1, y2), (x1 + corner_len, y2), box_color, thick)
            cv2.line(overlay, (x1, y2), (x1, y2 - corner_len), box_color, thick)
            # Bottom-right
            cv2.line(overlay, (x2, y2), (x2 - corner_len, y2), box_color, thick)
            cv2.line(overlay, (x2, y2), (x2, y2 - corner_len), box_color, thick)

            # Draw Centroid and Trajectory
            centroid = track.get("centroid")
            if centroid:
                cv2.circle(overlay, centroid, 4, box_color, -1)

            trajectory = track.get("trajectory", [])
            if len(trajectory) > 1:
                for i in range(1, len(trajectory)):
                    cv2.line(overlay, trajectory[i - 1], trajectory[i], box_color, 1, cv2.LINE_AA)

            # Label banner
            label_display = f"{label_text} ({int(confidence * 100)}%)"
            font_scale = 0.45
            (txt_w, txt_h), baseline = cv2.getTextSize(label_display, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
            banner_y1 = max(0, y1 - txt_h - 10)
            banner_y2 = y1
            cv2.rectangle(overlay, (x1, banner_y1), (x1 + txt_w + 10, banner_y2), box_color, -1)
            cv2.putText(overlay, label_display, (x1 + 5, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)

        # 3. HUD Header Bar (Semi-transparent top bar)
        header_h = 32
        hud = overlay.copy()
        cv2.rectangle(hud, (0, 0), (w, header_h), (18, 20, 28), -1)
        cv2.addWeighted(hud, 0.75, overlay, 0.25, 0, overlay)

        # Status text
        fps_text = f"FPS: {fps:.1f}" if fps > 0 else "FPS: --"
        cv2.putText(overlay, f"LIVE FEED | {camera_name.upper()} | {fps_text}", (15, 21),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 180), 1, cv2.LINE_AA)

        # Status indicator dot
        cv2.circle(overlay, (w - 20, 16), 6, (0, 255, 0), -1)

        return overlay

# Global detection service instance
detection_service = DetectionService()
