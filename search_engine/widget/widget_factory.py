from ..models import SearchContextWidget
from .codewidget import CodeStatsWidget
from .colorwidget import ColorPaletteWidget
from .gallerywidget import GalleryWidget
from .logwidget import LogAnalyzerWidget
from .widget_base import Widget

"""
    Central registry that evaluates which widgets should activate
    for a given SearchContext ->Factory pattern.
"""
class WidgetFactory:

    def __init__(self) -> None:
        self.widgets: list[Widget] = []

    def register(self, widget: Widget) -> None:
        self.widgets.append(widget) #add widget to the registry.


    def evaluate(self, ctx: SearchContextWidget) -> list[Widget]:
        #return all registered widgets whose activation rule matches the context.
        return [w for w in self.widgets if w.should_activate(ctx)]

def create_default_factory() -> WidgetFactory:
    #build a WidgetFactory pre loaded with all built in widgets.
    factory = WidgetFactory()
    factory.register(GalleryWidget())
    factory.register(LogAnalyzerWidget())
    factory.register(ColorPaletteWidget())
    factory.register(CodeStatsWidget())
    return factory

