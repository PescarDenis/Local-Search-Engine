from dataclasses import dataclass


@dataclass
class FileEntry:
    path: str
    filename: str
    extension: str
    size_bytes: int
    created_at: float
    modified_at: float
    mime_type: str
    content: str
    preview: str


@dataclass
class SearchResult:
    path: str
    filename: str
    preview: str
    modified_at: float
    score: float
