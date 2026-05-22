from ..models import SearchContextWidget, SearchResult
from ..query.history import SearchObserver
from .widget_base import Widget
from .widget_factory import WidgetFactory

"""Observer that subscribes to search result updates.
 When attached to the QueryEngine via engine.attach(), the CachedQueryEngine
 notification loop calls on_search() and on_results() automatically.
 Widget evaluation is triggered in on_results() once results are available."""


class WidgetObserver(SearchObserver):
    def __init__(self, factory: WidgetFactory) -> None:
        self.factory = factory
        self.active_widgets: list[Widget] = []
        self.last_ctx: SearchContextWidget | None = None

    # the on search method is triggered whenever a search query is performed
    # specifically for widgets, we reset to not get any stall data from the last search
    def on_search(self, raw_query: str) -> None:
        self.active_widgets = []
        self.last_ctx = None

    # called after results are available , builds context and evaluates widgets.
    def on_results(self, raw_query: str, results: list[SearchResult]) -> None:
        ctx = SearchContextWidget(raw_query=raw_query, results=results)
        self.active_widgets = self.factory.evaluate(ctx)
        self.last_ctx = ctx

    # the list of active widgets
    def get_active_widgets(self) -> list[Widget]:
        return list(self.active_widgets)

    # get method for returning the current context
    def get_last_context(self) -> SearchContextWidget | None:
        return self.last_ctx
