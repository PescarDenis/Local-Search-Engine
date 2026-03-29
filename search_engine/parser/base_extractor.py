from abc import ABC, abstractmethod
from pathlib import Path

class BaseExtractor(ABC):
    @abstractmethod
    def can_handle(self, mime_type: str) -> bool:
        pass

    @abstractmethod
    def extract(self, path: Path) -> tuple[str, str]:
        pass
