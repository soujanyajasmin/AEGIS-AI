import os
import uuid
import cv2
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from config import Config

class StorageService:
    def __init__(self, base_storage_dir=None):
        self.base_dir = Path(base_storage_dir or Config.STORAGE_DIR)
        self.snapshots_dir = self.base_dir / "snapshots"
        self.face_data_dir = self.base_dir / "face_data"
        self._ensure_directories()

    def _ensure_directories(self):
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.face_data_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, frame: np.ndarray, prefix: str = "event") -> str:
        """
        Saves a snapshot frame into storage/snapshots/YYYY/MM/DD/
        Returns the relative path from storage/
        """
        now = datetime.now(timezone.utc)
        date_dir = self.snapshots_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_{now.strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        full_path = date_dir / filename

        # Write image using OpenCV
        success = cv2.imwrite(str(full_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not success:
            raise IOError(f"Failed to write snapshot to {full_path}")

        # Return relative path for database storage (e.g. snapshots/2026/09/27/event_...)
        rel_path = full_path.relative_to(self.base_dir)
        return str(rel_path).replace("\\", "/")

    def save_face_sample(self, frame: np.ndarray, person_id: int) -> str:
        """
        Saves a face sample crop or frame into storage/face_data/
        Returns relative path
        """
        self.face_data_dir.mkdir(parents=True, exist_ok=True)
        filename = f"person_{person_id}_{uuid.uuid4().hex[:8]}.jpg"
        full_path = self.face_data_dir / filename

        success = cv2.imwrite(str(full_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not success:
            raise IOError(f"Failed to write face sample to {full_path}")

        rel_path = full_path.relative_to(self.base_dir)
        return str(rel_path).replace("\\", "/")

    def delete_file(self, rel_path: str) -> bool:
        """
        Safely deletes a file within the storage directory, preventing path traversal.
        """
        if not rel_path:
            return False

        # Normalize and resolve target path
        clean_rel = rel_path.strip().replace("\\", "/").lstrip("/")
        full_path = (self.base_dir / clean_rel).resolve()

        # Security check: must reside inside base_dir
        if not str(full_path).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Security error: path {rel_path} escapes storage root!")

        if full_path.exists() and full_path.is_file():
            try:
                full_path.unlink()
                return True
            except Exception as e:
                print(f"Error deleting file {full_path}: {e}")
                return False
        return False

    def get_storage_statistics(self) -> dict:
        """
        Computes disk storage statistics:
        - Snapshots total size (MB)
        - Snapshots count
        - Oldest snapshot timestamp
        - Face data size (MB)
        - Total storage used
        """
        total_snapshots_size = 0
        snapshots_count = 0
        oldest_snapshot_time = None

        if self.snapshots_dir.exists():
            for root, _, files in os.walk(self.snapshots_dir):
                for file in files:
                    if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        file_path = Path(root) / file
                        try:
                            stat = file_path.stat()
                            total_snapshots_size += stat.st_size
                            snapshots_count += 1
                            mtime = datetime.fromtimestamp(stat.st_mtime)
                            if oldest_snapshot_time is None or mtime < oldest_snapshot_time:
                                oldest_snapshot_time = mtime
                        except (OSError, FileNotFoundError):
                            continue

        total_face_size = 0
        face_count = 0
        if self.face_data_dir.exists():
            for file in self.face_data_dir.glob("*.*"):
                try:
                    stat = file.stat()
                    total_face_size += stat.st_size
                    face_count += 1
                except (OSError, FileNotFoundError):
                    continue

        total_bytes = total_snapshots_size + total_face_size
        return {
            "snapshots_count": snapshots_count,
            "snapshots_size_mb": round(total_snapshots_size / (1024 * 1024), 2),
            "face_data_count": face_count,
            "face_data_size_mb": round(total_face_size / (1024 * 1024), 2),
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "oldest_snapshot": oldest_snapshot_time.strftime("%Y-%m-%d %H:%M:%S") if oldest_snapshot_time else "None"
        }

# Global singleton instance
storage_service = StorageService()
