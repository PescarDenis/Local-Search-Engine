import time
from dataclasses import dataclass, field

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

@dataclass
class IndexReport:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: int = 0
    _start_time: float = field(default_factory=time.time)

    def add(self, status: str) -> None:
        match status:
            case "inserted": self.inserted += 1
            case "updated":  self.updated += 1
            case "skipped":  self.skipped += 1
            case "deleted":  self.deleted += 1
            case "error":    self.errors += 1

    def print_report(self) -> str:
        duration = time.time() - self._start_time
        total = self.inserted + self.updated + self.skipped + self.deleted
        return (
            f"\nIndexing complete\n"
            f"{'─' * 30}\n"
            f"  Inserted : {self.inserted}\n"
            f"  Updated  : {self.updated}\n"
            f"  Skipped  : {self.skipped}\n"
            f"  Deleted  : {self.deleted}\n"
            f"  Errors   : {self.errors}\n"
            f"{'─' * 30}\n"
            f"  Total    : {total}\n"
            f"  Duration : {duration:.1f}s\n"
        )
