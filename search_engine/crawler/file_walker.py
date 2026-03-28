import os
from pathlib import Path
from typing import Iterator

from .ignore_filter import IgnoreFilter


class FileWalker:

    def __init__(self, ignore_filter: IgnoreFilter) -> None:
        self._filter = ignore_filter

    def walk(self, root: Path) -> Iterator[Path]:
        visited_inodes: set[int] = set()

        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            current = Path(dirpath)

            try:
                inode = current.stat().st_ino
            except OSError:
                dirnames.clear()
                continue

            if inode in visited_inodes:
                dirnames.clear()
                continue
            visited_inodes.add(inode)

            dirnames[:] = [
                d for d in dirnames
                if not self._filter.should_ignore(current / d)
            ]

            for filename in filenames:
                file_path = current / filename
                if not self._filter.should_ignore(file_path):
                    yield file_path
