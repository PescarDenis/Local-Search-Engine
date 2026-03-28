import fnmatch
from pathlib import Path


class IgnoreFilter:

    def __init__(self, patterns: list[str]) -> None:
        self._patterns = patterns

    def should_ignore(self, path: Path) -> bool:
        for part in path.parts:
            for pattern in self._patterns:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False
