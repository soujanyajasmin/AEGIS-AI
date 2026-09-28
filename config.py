import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Flask Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "premises-security-super-secret-key-2026-secure")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # Database
    db_env = os.environ.get("DATABASE_URL")
    if db_env and not db_env.startswith("sqlite:///instance/"):
        SQLALCHEMY_DATABASE_URI = db_env
    else:
        db_path = (BASE_DIR / "instance" / "security.db").resolve().as_posix()
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Storage Paths
    STORAGE_DIR = BASE_DIR / "storage"
    SNAPSHOTS_DIR = STORAGE_DIR / "snapshots"
    FACE_DATA_DIR = STORAGE_DIR / "face_data"
    MODELS_DIR = BASE_DIR / "models_data"

    # Computer Vision & Detection Defaults
    CAMERA_SOURCE = os.environ.get("CAMERA_SOURCE", "0")
    FRAME_SKIP = int(os.environ.get("FRAME_SKIP", "2"))
    DETECTION_INTERVAL = float(os.environ.get("DETECTION_INTERVAL", "0.05"))
    DETECTION_CONFIDENCE = float(os.environ.get("DETECTION_CONFIDENCE", "0.45"))
    FACE_RECOGNITION_THRESHOLD = float(os.environ.get("FACE_RECOGNITION_THRESHOLD", "0.40"))
    EVENT_COOLDOWN = int(os.environ.get("EVENT_COOLDOWN", "30"))  # seconds before repeating event
    RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))

    # Tracking & Line Crossing
    LINE_POSITION = float(os.environ.get("LINE_POSITION", "0.50")) # 50% frame height
    LINE_ORIENTATION = os.environ.get("LINE_ORIENTATION", "horizontal")

    # Allowed Upload Extensions
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
