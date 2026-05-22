import os
import re
import time
from dataclasses import dataclass, field
from collections import Counter


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
    color: str = ""
    weight: float = 1.0


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
            case "inserted":
                self.inserted += 1
            case "updated":
                self.updated += 1
            case "skipped":
                self.skipped += 1
            case "deleted":
                self.deleted += 1
            case "error":
                self.errors += 1

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


"""
Normally, the widgets needs to analyze the results after are results are returned from the query.
We are going to build a new class, that will act as a DTO which decides which widget to activate
and not modify the current logic

->SearchContextWidget does the analysis for which widget to activate all at once and exposes the results
"""
IMAGE_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
}
LOG_EXT = {".log"}
CODE_EXT = {
    ".py",
    ".js",
    ".ts",
    ".cpp",
    "cpp.o.d",
    "cpp.o" ".c",
    ".h",
    ".go",
    ".rs",
    ".java",
}


@dataclass
class SearchContextWidget:
    raw_query: str  # raw query
    results: list[SearchResult]  # results returned from the query

    # computed fields
    extension_counts: Counter = field(
        default_factory=Counter
    )  # count how many extensions we found
    dominant_extension: str | None = None  # determine which one is the dominant  ext
    has_color_query: bool = False  # color widget if we input a query with "color"
    image_ratio: float = 0.0
    log_ratio: float = 0.0
    code_ratio: float = 0.0

    def __post_init__(self) -> None:
        self._compute_extension_stats()

    # private function to determine the stats
    def _compute_extension_stats(self) -> None:
        if not self.results:
            return

        for r in self.results:
            ext = os.path.splitext(r.path)[1].lower()
            self.extension_counts[ext] += 1

        total = len(self.results)
        self.dominant_extension = (
            self.extension_counts.most_common(1)[0][0]
            if self.extension_counts
            else None
        )

        image_count = sum(self.extension_counts[e] for e in IMAGE_EXT)
        log_count = sum(self.extension_counts[e] for e in LOG_EXT)
        code_count = sum(self.extension_counts[e] for e in CODE_EXT)

        self.image_ratio = image_count / total
        self.log_ratio = log_count / total
        self.code_ratio = code_count / total
        self.has_color_query = bool(re.search(r"color:", self.raw_query))
