from pathlib import Path
from ..models import FileEntry
from .metadata_extractor import MetadataExtractor
from .text_extractor import TextExtractor
from .scorer import FileScorer

class FileParser:

    def __init__(self, extractors=None, metadata=None, scorer=None):
        self.extractors = extractors or [TextExtractor()]
        self.metadata = metadata or MetadataExtractor()
        self.scorer = scorer or FileScorer()

    def parse(self, path: Path) -> FileEntry | None:
        try:
            meta = self.metadata.extract(path)
        except Exception:
            return None
        content, preview = "", ""
        for ext in self.extractors:
            if ext.can_handle(meta["mime_type"]):
                content, preview = ext.extract(path)
                break

        return FileEntry(
            path=str(path),
            filename=meta["filename"],
            extension=meta["extension"],
            size_bytes=meta["size_bytes"],
            created_at=meta["created_at"],
            modified_at=meta["modified_at"],
            mime_type=meta["mime_type"],
            content=content,
            preview=preview,
            weight=self.scorer.score(path, meta["size_bytes"], meta["modified_at"]),
        )