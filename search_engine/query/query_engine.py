from ..database.connection import get_connection
from ..models import SearchResult
from .query_parser import QueryParser
from .result_formatter import ResultFormatter

class QueryEngine:

    def __init__(
        self,
        db_path: str,
        max_results: int,
        snippet_tokens: int,
        parser: QueryParser | None = None,
        formatter: ResultFormatter | None = None,
    ) -> None:
        self._db_path = db_path
        self._max_results = max_results
        self._snippet_tokens = snippet_tokens
        self._parser = parser or QueryParser()
        self._formatter = formatter or ResultFormatter()

    def search(self, raw_query: str) -> list[SearchResult]:
        fts_query = self._parser.parse(raw_query)
        if fts_query is None:
            return []

        rows = self._run_query(fts_query)
        return self._formatter.format(rows)

    def _run_query(self, fts_query: str) -> list:
        sql = """
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
            ORDER BY combined_score ASC
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
