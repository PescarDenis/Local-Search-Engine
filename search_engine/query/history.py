import time
from abc import ABC, abstractmethod
from ..database.connection import get_connection

class SearchObserver(ABC):
    #Observer interface for tracking search activity
    #Any class that wants to react to a search being performed should inherit this
    @abstractmethod
    def on_search(self, raw_query: str) -> None:
        pass

class HistoryTracker(SearchObserver):
    def __init__(self, db_path: str):
        self._db_path = db_path
        
    def on_search(self, raw_query: str) -> None:
        #Triggered automatically by the QueryEngine every time a search is performed
        query = raw_query.strip().lower()
        if not query:
            return
            
        now = time.time()

        #Insert logic -> If the query already exists, just increase the frequency counter and  update timestamp
        sql = """
            INSERT INTO search_history (query, search_count, timestamp)
            VALUES (?, 1, ?)
            ON CONFLICT(query) DO UPDATE SET 
                search_count = search_count + 1,
                timestamp = excluded.timestamp
        """
        try:
            with get_connection(self._db_path) as conn:
                conn.execute(sql, (query, now))
        except Exception:
            pass

    def get_suggestions(self, prefix: str, limit: int = 5) -> list[str]:
        #Provides autocomplete-style query suggestions based on past search frequency
        prefix = prefix.strip().lower()
        sql = """
            SELECT query FROM search_history 
            WHERE query LIKE ?
            ORDER BY search_count DESC, timestamp DESC
            LIMIT ?
        """
        try:
            with get_connection(self._db_path) as conn:
                rows = conn.execute(sql, (f"{prefix}%", limit)).fetchall()
            return [row["query"] for row in rows]
        except Exception:
            return []
            
    def get_top_queries(self, limit: int = 5) -> list[str]:
        sql = """
            SELECT query FROM search_history 
            ORDER BY search_count DESC, timestamp DESC
            LIMIT ?
        """
        try:
            with get_connection(self._db_path) as conn:
                rows = conn.execute(sql, (limit,)).fetchall()
            return [row["query"] for row in rows]
        except Exception:
            return []
