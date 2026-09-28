from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from sqlalchemy import func
from models import db, Event, Person, Camera, Notification
from routes import login_required
from services.camera_service import camera_service
from services.storage_service import storage_service

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    # Fetch today's summary metrics
    today_start = datetime.combine(date.today(), datetime.min.time())

    today_events_count = Event.query.filter(Event.timestamp >= today_start).count()
    people_detected = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON").count()
    known_people = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON", Event.recognition_status == "KNOWN").count()
    unknown_people = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON", Event.recognition_status == "UNKNOWN").count()
    vehicles_count = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "VEHICLE").count()
    animals_count = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "ANIMAL").count()

    # Storage statistics
    storage_stats = storage_service.get_storage_statistics()

    # Recent 10 events
    recent_events = Event.query.order_by(Event.timestamp.desc()).limit(10).all()

    # Available cameras
    cameras = Camera.query.all()

    return render_template(
        "dashboard.html",
        today_events=today_events_count,
        people_detected=people_detected,
        known_people=known_people,
        unknown_people=unknown_people,
        vehicles_count=vehicles_count,
        animals_count=animals_count,
        storage_stats=storage_stats,
        recent_events=recent_events,
        cameras=cameras,
        camera_status=camera_service.get_status()
    )

@dashboard_bp.route("/api/statistics")
@login_required
def api_statistics():
    today_start = datetime.combine(date.today(), datetime.min.time())

    today_events_count = Event.query.filter(Event.timestamp >= today_start).count()
    people_detected = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON").count()
    known_people = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON", Event.recognition_status == "KNOWN").count()
    unknown_people = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "PERSON", Event.recognition_status == "UNKNOWN").count()
    vehicles_count = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "VEHICLE").count()
    animals_count = Event.query.filter(Event.timestamp >= today_start, Event.entity_type == "ANIMAL").count()

    # Hourly distribution for Chart.js
    hourly_counts = {f"{h:02d}:00": 0 for h in range(24)}
    events_today = Event.query.filter(Event.timestamp >= today_start).all()
    for ev in events_today:
        hour_key = ev.timestamp.strftime("%H:00")
        if hour_key in hourly_counts:
            hourly_counts[hour_key] += 1

    storage_stats = storage_service.get_storage_statistics()

    recent_events = [e.to_dict() for e in Event.query.order_by(Event.timestamp.desc()).limit(8).all()]

    return jsonify({
        "status": "success",
        "metrics": {
            "today_events": today_events_count,
            "people_detected": people_detected,
            "known_people": known_people,
            "unknown_people": unknown_people,
            "vehicles": vehicles_count,
            "animals": animals_count,
            "storage_used_mb": storage_stats["total_size_mb"]
        },
        "hourly_chart": {
            "labels": list(hourly_counts.keys()),
            "data": list(hourly_counts.values())
        },
        "storage": storage_stats,
        "recent_events": recent_events,
        "camera_status": camera_service.get_status()
    })
