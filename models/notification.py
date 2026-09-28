from datetime import datetime
from . import db

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=True, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default="warning", nullable=False) # 'critical', 'warning', 'info'
    read_status = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        snapshot_url = ""
        if self.event and self.event.snapshot_path:
            snapshot_url = f"/storage/{self.event.snapshot_path}"

        return {
            "id": self.id,
            "event_id": self.event_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "read_status": self.read_status,
            "snapshot_url": snapshot_url,
            "camera_name": self.event.camera.name if self.event and self.event.camera else "Camera #1",
            "date": self.created_at.strftime("%Y-%m-%d"),
            "time": self.created_at.strftime("%H:%M:%S"),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self):
        return f"<Notification #{self.id} {self.title} (Read={self.read_status})>"
