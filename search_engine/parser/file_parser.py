from pathlib import Path
from ..models import FileEntry
from .metadata_extractor import MetadataExtractor
from .text_extractor import TextExtractor
from .image_extractor import ImageExtractor
from .scorer import FileScorer


class FileParser:

    def __init__(self, extractors=None, metadata=None, scorer=None):
        self.extractors = extractors or [TextExtractor(), ImageExtractor()]
        self.metadata = metadata or MetadataExtractor()
        self.scorer = scorer or FileScorer()

    def parse(self, path: Path) -> FileEntry | None:
        try:
            meta = self.metadata.extract(path)
        except Exception:
            return None
        extracted = None
        for ext in self.extractors:
            if ext.can_handle(meta["mime_type"]):
                extracted = ext.extract(path)
                break

        # If no extractor can handle this file type, skip it entirely
        if extracted is None:
            return None

        return FileEntry(
            path=str(path),
            filename=meta["filename"],
            extension=meta["extension"],
            size_bytes=meta["size_bytes"],
            created_at=meta["created_at"],
            modified_at=meta["modified_at"],
            mime_type=meta["mime_type"],
            content=extracted.get("content", ""),
            preview=extracted.get("preview", ""),
            color=extracted.get("color", ""),
            weight=self.scorer.score(path, meta["size_bytes"], meta["modified_at"]),
        )
