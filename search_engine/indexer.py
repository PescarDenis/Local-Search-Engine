from pathlib import Path
from .crawler.file_walker import FileWalker
from .crawler.ignore_filter import IgnoreFilter
from .database.schema import initialise
from .index.index_manager import IndexManager
from .models import IndexReport
from .parser.file_parser import FileParser

class Indexer:

    def __init__(
        self,
        db_path: str,
        ignore_patterns: list[str],
        walker: FileWalker | None = None,
        parser: FileParser | None = None,
        manager: IndexManager | None = None,
    ) -> None:
        self._db_path = db_path
        ignore_filter = IgnoreFilter(ignore_patterns)
        self._walker = walker or FileWalker(ignore_filter)
        self._parser = parser or FileParser()
        self._manager = manager or IndexManager(db_path)

    def run(self, root: Path) -> IndexReport:
        initialise(self._db_path)

        report = IndexReport()
        indexed_paths: set[str] = set()

        for file_path in self._walker.walk(root):
            record = self._parser.parse(file_path)

            if record is None:
                report.add("error")
                continue

            indexed_paths.add(record.path)

            try:
                self._manager.process(record, report)
            except Exception:
                report.add("error")

        self._manager.delete_stale(indexed_paths, report)

        return report
