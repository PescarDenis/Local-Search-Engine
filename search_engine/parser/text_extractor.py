import chardet
from pathlib import Path
from .base_extractor import BaseExtractor

class TextExtractor(BaseExtractor):
    #MIME types that do not start with text but we still want to read
    VALID_TYPES = {
        "application/json",
        "application/xml",
        "application/x-sh",
        "application/x-python",
        "application/javascript",
    }

    def can_handle(self, mime_type: str) -> bool:
        if mime_type.startswith("text/"):
            return True
        return mime_type in self.VALID_TYPES

    def extract(self, path: Path) -> tuple[str, str]:
        encoding = self._guess_encoding(path)
        if not encoding:
            return "", ""

        try:
            with open(path, "r", encoding=encoding) as f:
                lines = f.readlines()

            content = "".join(lines).strip()
            preview = "".join(lines[:3]).strip()

            return content, preview

        except OSError:
            return "", ""

    def _guess_encoding(self, path: Path) -> str | None:
        try:
            raw = path.read_bytes()[:8192]  #Read 8KB to figure out the encoding of the fil
        except OSError:
            return None

        if b"\x00" in raw: # if this is a binary file
            return None

        guessed = chardet.detect(raw)
        return guessed.get("encoding") or "utf-8"