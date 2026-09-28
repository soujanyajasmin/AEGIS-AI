from flask import Blueprint, render_template, request, jsonify
from models import db, Camera
from routes import login_required, admin_required
from services.camera_service import camera_service

cameras_bp = Blueprint("cameras", __name__)

@cameras_bp.route("/cameras")
@login_required
def index():
    cameras = Camera.query.all()
    return render_template("cameras.html", cameras=cameras)

@cameras_bp.route("/api/cameras", methods=["GET"])
@login_required
def list_cameras():
    cameras = Camera.query.all()
    return jsonify([c.to_dict() for c in cameras])

@cameras_bp.route("/api/cameras", methods=["POST"])
@login_required
@admin_required
def create_camera():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    source = str(data.get("source", "0")).strip()
    source_type = data.get("source_type", "webcam")
    resolution = data.get("resolution", "640x480")
    fps = int(data.get("fps", 25))
    conf_thresh = float(data.get("confidence_threshold", 0.45))
    face_thresh = float(data.get("face_threshold", 0.40))
    line_orient = data.get("line_orientation", "horizontal")
    line_pos = float(data.get("line_position", 0.50))
    enabled = bool(data.get("enabled", True))

    if not name or not source:
        return jsonify({"status": "error", "message": "Name and Source are required"}), 400

    cam = Camera(
        name=name,
        source=source,
        source_type=source_type,
        resolution=resolution,
        fps=fps,
        confidence_threshold=conf_thresh,
        face_threshold=face_thresh,
        line_orientation=line_orient,
        line_position=line_pos,
        enabled=enabled
    )
    db.session.add(cam)
    db.session.commit()

    return jsonify({"status": "success", "message": "Camera added successfully", "camera": cam.to_dict()})

@cameras_bp.route("/api/cameras/<int:id>", methods=["GET"])
@login_required
def get_camera(id):
    cam = Camera.query.get_or_404(id)
    return jsonify({"status": "success", "camera": cam.to_dict()})

@cameras_bp.route("/api/cameras/<int:id>", methods=["PUT"])
@login_required
@admin_required
def update_camera(id):
    cam = Camera.query.get_or_404(id)
    data = request.get_json() or {}

    if "name" in data and data["name"].strip():
        cam.name = data["name"].strip()
    if "source" in data and str(data["source"]).strip():
        cam.source = str(data["source"]).strip()
    if "source_type" in data:
        cam.source_type = data["source_type"]
    if "resolution" in data:
        cam.resolution = data["resolution"]
    if "fps" in data:
        cam.fps = int(data["fps"])
    if "confidence_threshold" in data:
        cam.confidence_threshold = float(data["confidence_threshold"])
    if "face_threshold" in data:
        cam.face_threshold = float(data["face_threshold"])
    if "line_orientation" in data:
        cam.line_orientation = data["line_orientation"]
    if "line_position" in data:
        cam.line_position = float(data["line_position"])
    if "enabled" in data:
        cam.enabled = bool(data["enabled"])

    db.session.commit()

    # If this is the active camera, update camera service parameters immediately
    if camera_service.camera_id == cam.id:
        camera_service.configure_from_camera(cam)

    return jsonify({"status": "success", "message": "Camera updated successfully", "camera": cam.to_dict()})

@cameras_bp.route("/api/cameras/<int:id>", methods=["DELETE"])
@login_required
@admin_required
def delete_camera(id):
    cam = Camera.query.get_or_404(id)
    db.session.delete(cam)
    db.session.commit()
    return jsonify({"status": "success", "message": f"Camera '{cam.name}' deleted"})
