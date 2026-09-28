import time
import threading
from datetime import datetime
from typing import Optional, Dict, Tuple
import numpy as np
from config import Config
from models import db, Event, Camera, Person, SystemSetting
from services.storage_service import storage_service
from services.notification_service import notification_service

class EventService:
    def __init__(self):
        # Cooldown map: (entity_type, identifier, event_sub_type) -> float (timestamp)
        self.cooldown_tracker: Dict[Tuple[str, str, str], float] = {}
        self.lock = threading.Lock()

    def get_cooldown_seconds(self) -> int:
        try:
            val = SystemSetting.get("EVENT_COOLDOWN", str(Config.EVENT_COOLDOWN))
            return max(5, int(val))
        except Exception:
            return Config.EVENT_COOLDOWN

    def should_record_event(self, entity_type: str, identifier: str, event_type: str) -> bool:
        """
        Checks if cooldown has elapsed for this entity and event type.
        """
        key = (entity_type, str(identifier), event_type)
        now = time.time()
        cooldown = self.get_cooldown_seconds()

        with self.lock:
            # Clean up old tracker keys if list gets large (> 2000)
            if len(self.cooldown_tracker) > 2000:
                cutoff = now - 3600
                self.cooldown_tracker = {k: v for k, v in self.cooldown_tracker.items() if v > cutoff}

            last_time = self.cooldown_tracker.get(key, 0.0)
            if (now - last_time) >= cooldown:
                self.cooldown_tracker[key] = now
                return True
            return False

    def record_detection_event(
        self,
        frame: np.ndarray,
        camera_id: Optional[int],
        entity_type: str,
        entity_name: str,
        recognition_status: str = "NOT_APPLICABLE",
        person_id: Optional[int] = None,
        event_type: str = "DETECTION",
        direction: str = "NONE",
        confidence: float = 0.0,
        metadata: Optional[dict] = None
    ) -> Optional[Event]:
        """
        Evaluates event cooldown, saves snapshot, writes Event to database,
        and triggers notifications for critical/relevant entities.
        """
        # Determine unique identifier for de-duplication
        # For known person: person_id or name. For unknown person: 'unknown'. For vehicles: entity_name.
        identifier = person_id if person_id else entity_name
        
        # Line crossings (ENTRY / EXIT) are important transitions
        effective_event_type = direction if direction in ["ENTRY", "EXIT"] else event_type

        # Check cooldown
        if not self.should_record_event(entity_type, identifier, effective_event_type):
            return None

        # Capture and save snapshot image to storage/snapshots/YYYY/MM/DD/
        snapshot_rel_path = ""
        if frame is not None and frame.size > 0:
            try:
                prefix = f"{entity_type.lower()}_{effective_event_type.lower()}"
                snapshot_rel_path = storage_service.save_snapshot(frame, prefix=prefix)
            except Exception as e:
                print(f"[EventService] Error saving snapshot: {e}")

        try:
            new_event = Event(
                camera_id=camera_id,
                person_id=person_id,
                entity_type=entity_type,
                entity_name=entity_name,
                recognition_status=recognition_status,
                event_type=effective_event_type,
                direction=direction,
                confidence=float(confidence),
                snapshot_path=snapshot_rel_path,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_event)
            db.session.commit()

            # Trigger real-time notifications for important events
            self._handle_event_notification(new_event)
            return new_event

        except Exception as e:
            db.session.rollback()
            print(f"[EventService] Database error saving event: {e}")
            return None

    def _handle_event_notification(self, event: Event):
        """
        Dispatches alerts based on detection and recognition rules.
        """
        cam_name = event.camera.name if event.camera else "Camera #1"
        time_str = event.timestamp.strftime("%H:%M:%S")

        # 1. Unknown Person: High Priority Alert
        if event.entity_type == "PERSON" and event.recognition_status == "UNKNOWN":
            title = "🚨 UNKNOWN PERSON DETECTED"
            msg = f"Unknown individual detected at {cam_name} ({time_str})"
            if event.direction != "NONE":
                msg += f" - Direction: {event.direction}"
            notification_service.create_notification(title, msg, severity="critical", event_id=event.id)

        # 2. Known Person Line Crossing
        elif event.entity_type == "PERSON" and event.recognition_status == "KNOWN" and event.direction in ["ENTRY", "EXIT"]:
            title = f"👤 {event.entity_name} - {event.direction}"
            msg = f"{event.entity_name} entered or exited via {cam_name} at {time_str}"
            notification_service.create_notification(title, msg, severity="info", event_id=event.id)

        # 3. Vehicle Detected
        elif event.entity_type == "VEHICLE":
            title = f"🚗 Vehicle Detected ({event.entity_name.capitalize()})"
            msg = f"{event.entity_name.capitalize()} observed at {cam_name} at {time_str}"
            if event.direction != "NONE":
                msg += f" ({event.direction})"
            notification_service.create_notification(title, msg, severity="warning", event_id=event.id)

        # 4. Animal Detected
        elif event.entity_type == "ANIMAL":
            title = f"🐾 Animal Alert ({event.entity_name.capitalize()})"
            msg = f"{event.entity_name.capitalize()} detected within premises boundary at {time_str}"
            notification_service.create_notification(title, msg, severity="info", event_id=event.id)

event_service = EventService()
