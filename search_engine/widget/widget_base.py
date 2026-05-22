from abc import ABC, abstractmethod
from ..models import SearchContextWidget

"""
    Base class for all widgets.
    Each subclass encapsulates its own activation rule and rendering logic.
"""


class Widget(ABC):

    @property
    @abstractmethod
    # name of the widget
    def name(self) -> str:
        pass

    @abstractmethod
    # return true if the widget is relevant for the given search context
    def should_activate(self, ctx: SearchContextWidget) -> bool:
        pass

    @abstractmethod
    # produce the CLI string printing for the widget
    def render(self, ctx: SearchContextWidget) -> str:
        pass
