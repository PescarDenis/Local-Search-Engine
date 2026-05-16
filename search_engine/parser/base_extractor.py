from abc import ABC, abstractmethod
from pathlib import Path

class BaseExtractor(ABC):
    @abstractmethod
    def can_handle(self, mime_type: str) -> bool:
        pass

    @abstractmethod
    #return a dict instead of a tuple because it is more scalabale
    #we can now return content : ... , preview:.... ,color ... etc.
    def extract(self, path: Path) -> dict[str, str]:
        pass
