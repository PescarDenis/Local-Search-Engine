from pathlib import Path
from ..database.connection import get_connection
from ..models import FileEntry,IndexReport
from .timestamp_detector import TimestampChangeDetection

class IndexManager:

    def __init__(self,db_path: str,detector: TimestampChangeDetection | None = None) -> None:
        self._db_path = db_path
        self._detector = detector or TimestampChangeDetection(db_path)

    def process(self, entry: FileEntry, report: IndexReport) -> None:
        stored_mtime = self._detector.get_stored_mtime(Path(entry.path))

        if stored_mtime is None:
            self._insert(entry)
            report.add("inserted")

        elif self._detector.has_changed(Path(entry.path), stored_mtime):
            self._update(entry)
            report.add("updated")

        else:
            report.add("skipped")

    def delete_stale(self, indexed_paths: set[str], report: IndexReport) -> None:
        with get_connection(self._db_path) as conn:
            stored = {row["path"] for row in conn.execute("SELECT path FROM files").fetchall()}

        stale = stored - indexed_paths
        for path in stale:
            self._delete(path)
            report.add("deleted")

    def _insert(self, entry: FileEntry) -> None:
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO files
                    (path, filename, extension, size_bytes, mime_type,
                     created_at, modified_at, preview, content, weight)
                VALUES
                    (:path, :filename, :extension, :size_bytes, :mime_type,
                     :created_at, :modified_at, :preview, :content, :weight)
                """,
                entry.__dict__
            )

    def _update(self, entry: FileEntry) -> None:
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                UPDATE files SET
                    filename    = :filename,
                    extension   = :extension,
                    size_bytes  = :size_bytes,
                    mime_type   = :mime_type,
                    created_at  = :created_at,
                    modified_at = :modified_at,
                    preview     = :preview,
                    content     = :content,
                    weight      = :weight
                WHERE path = :path
                """,
               entry.__dict__
            )

    def _delete(self, path: str) -> None:
        with get_connection(self._db_path) as conn:
            conn.execute("DELETE FROM files WHERE path = ?", (path,))
