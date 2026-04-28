from ..database.connection import get_connection
from ..models import SearchResult
from .query_parser import QueryParser
from .result_formatter import ResultFormatter
from .ranking import RankingStrategy, RelevanceRanking
from .history import SearchObserver

class QueryEngine:

    def __init__(
        self,
        db_path: str,
        max_results: int,
        snippet_tokens: int,
        parser: QueryParser | None = None,
        formatter: ResultFormatter | None = None,
        strategy: RankingStrategy | None = None,
    ) -> None:
        self._db_path = db_path
        self._max_results = max_results
        self._snippet_tokens = snippet_tokens
        self._parser = parser or QueryParser()
        self._formatter = formatter or ResultFormatter()
        self._strategy = strategy or RelevanceRanking()
        self._observers: list[SearchObserver] = []

    def strategy_name(self) -> str:
        return type(self._strategy).__name__

    def attach(self, observer: SearchObserver) -> None:
        # subscribes a generic observer -> HistoryTracker to listen to queries
        self._observers.append(observer)
    """
    Deprecated method used before for the query engine search but now if there is a cache miss --->
    normal flow of the query engine execute search is called which searches the query
    def search(self, raw_query: str) -> list[SearchResult]:
        # notify all subscribed trackers that a search is occurring
        for observer in self._observers:
            observer.on_search(raw_query)

        return self._execute_search(raw_query)
    """

    #search logic separated so the caching proxy can call it without re-notifying observers
    def _execute_search(self, raw_query: str) -> list[SearchResult]:
        fts_query = self._parser.parse(raw_query)
        if fts_query is None:
            return []

        rows = self._run_query(fts_query)
        results = self._formatter.format(rows)
        
        # allow the active sorting strategy to manually tweak the results
        return self._strategy.apply_ranking(results)

    def _run_query(self, fts_query: str) -> list:
        order_clause = self._strategy.get_order_by()
        sql = f"""
            SELECT
                f.path,
                f.filename,
                f.modified_at,
                f.preview,
                (fts.rank * f.weight) AS combined_score,
                snippet(files_fts, 2, '[', ']', '...', :tokens) AS snippet           
            FROM files_fts fts
            JOIN files f ON f.id = fts.rowid
            WHERE files_fts MATCH :query
            ORDER BY {order_clause}
            LIMIT :limit
        """
        try:
            with get_connection(self._db_path) as conn:
                rows = conn.execute(
                    sql,
                    {
                        "query":  fts_query,
                        "tokens": self._snippet_tokens,
                        "limit":  self._max_results,
                    },
                ).fetchall()
            return rows
        except Exception:
            return []
