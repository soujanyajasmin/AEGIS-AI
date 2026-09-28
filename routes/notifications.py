import json
import time
from flask import Blueprint, render_template, jsonify, Response, request
from models import db, Notification
from routes import login_required
from services.notification_service import notification_service

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications")
@login_required
def index():
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(100).all()
    return render_template("notifications.html", notifications=notifications)

@notifications_bp.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    limit = request.args.get("limit", 20, type=int)
    notifs = notification_service.get_recent(limit=limit, unread_only=unread_only)
    return jsonify({
        "status": "success",
        "notifications": notifs,
        "unread_count": notification_service.get_unread_count()
    })

@notifications_bp.route("/api/notifications/<int:id>/read", methods=["POST"])
@login_required
def mark_read(id):
    success = notification_service.mark_as_read(id)
    return jsonify({"status": "success" if success else "error"})

@notifications_bp.route("/api/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    count = notification_service.mark_all_as_read()
    return jsonify({"status": "success", "marked_count": count})

@notifications_bp.route("/api/notifications/stream")
@login_required
def sse_stream():
    """Server-Sent Events endpoint for real-time notification push to frontend"""
    q = notification_service.subscribe()

    def event_stream():
        try:
            # Send initial keepalive
            yield f": keepalive\n\n"
            while True:
                try:
                    # Wait up to 20 seconds for new notification
                    notif_data = q.get(timeout=20.0)
                    yield f"data: {json.dumps(notif_data)}\n\n"
                except Exception:
                    # Send periodic heartbeat so connection stays open
                    yield f": ping\n\n"
        finally:
            notification_service.unsubscribe(q)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
