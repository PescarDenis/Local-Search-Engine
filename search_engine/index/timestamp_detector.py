from pathlib import Path
from ..database.connection import get_connection

class TimestampChangeDetection:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def get_stored_mtime(self, path: Path) -> float | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute("SELECT modified_at FROM files WHERE path = ?",(str(path),)).fetchone()
        return row["modified_at"] if row else None

    def has_changed(self, path: Path, stored_mtime: float) -> bool:
        try:
            current_mtime = path.stat().st_mtime
            return current_mtime != stored_mtime
        except OSError:
            return False
