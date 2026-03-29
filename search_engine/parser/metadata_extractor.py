import mimetypes
from pathlib import Path

class MetadataExtractor:
    def extract(self, path: Path) -> dict:
        try:
            stat = path.stat()
            size_bytes = stat.st_size
            created_at = stat.st_ctime
            modified_at = stat.st_mtime
        except OSError:
            size_bytes = 0
            created_at = 0.0
            modified_at = 0.0

        mime_type, _ = mimetypes.guess_type(str(path))

        return {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": size_bytes,
            "created_at": created_at,
            "modified_at": modified_at,
            "mime_type": mime_type or "application/octet-stream",
        }
