import json
import queue
import threading
from datetime import datetime
from typing import List, Optional
from models import db, Notification, Event

class NotificationService:
    def __init__(self):
        # Thread-safe queue for SSE broadcast
        self.listeners: List[queue.Queue] = []
        self.lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        """Subscribes a client to the real-time notification stream (SSE)"""
        q = queue.Queue(maxsize=50)
        with self.lock:
            self.listeners.append(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        with self.lock:
            if q in self.listeners:
                self.listeners.remove(q)

    def broadcast(self, notification_data: dict):
        """Pushes notification payload to all active SSE subscribers"""
        with self.lock:
            dead_listeners = []
            for q in self.listeners:
                try:
                    q.put_nowait(notification_data)
                except queue.Full:
                    dead_listeners.append(q)
            for q in dead_listeners:
                if q in self.listeners:
                    self.listeners.remove(q)

    def create_notification(self, title: str, message: str, severity: str = "warning", event_id: Optional[int] = None) -> Notification:
        """
        Creates and persists a notification in DB and broadcasts it to live clients.
        """
        try:
            notif = Notification(
                event_id=event_id,
                title=title,
                message=message,
                severity=severity,
                read_status=False
            )
            db.session.add(notif)
            db.session.commit()

            # Prepare broadcast payload
            payload = notif.to_dict()
            self.broadcast(payload)
            return notif
        except Exception as e:
            db.session.rollback()
            print(f"[NotificationService] Error creating notification: {e}")
            return None

    def get_recent(self, limit: int = 20, unread_only: bool = False) -> List[dict]:
        query = Notification.query.order_by(Notification.created_at.desc())
        if unread_only:
            query = query.filter_by(read_status=False)
        notifications = query.limit(limit).all()
        return [n.to_dict() for n in notifications]

    def get_unread_count(self) -> int:
        return Notification.query.filter_by(read_status=False).count()

    def mark_as_read(self, notification_id: int) -> bool:
        notif = Notification.query.get(notification_id)
        if notif:
            notif.read_status = True
            db.session.commit()
            return True
        return False

    def mark_all_as_read(self) -> int:
        count = Notification.query.filter_by(read_status=False).update({"read_status": True})
        db.session.commit()
        return count

notification_service = NotificationService()
