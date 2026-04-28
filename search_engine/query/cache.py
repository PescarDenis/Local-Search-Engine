import json
import time
from ..database.connection import get_connection
from ..models import SearchResult
from .query_engine import QueryEngine

class SearchCache:
    #disk based cache that stores serialized search results in the cache_results table
    def __init__(self, db_path: str, ttl_seconds: float = 300.0):
        self._db_path = db_path #path to the index.db
        self._ttl = ttl_seconds #init TTL to prevent outdating res
        self._last_hit = False #determine whether the res is cached or not

    def get(self, key: str) -> list[SearchResult] | None:
        #returns cached results if the entry exists and has not expired, None otherwise
        sql = "SELECT results, created_at FROM cache_results WHERE cache_key = ?"
        try:
            with get_connection(self._db_path) as conn:
                row = conn.execute(sql, (key,)).fetchone()
        except Exception:
            self._last_hit = False
            return None

        if row is None:
            self._last_hit = False
            return None

        #check if the cached entry has expired based on TTL
        if time.time() - row["created_at"] > self._ttl:
            self._remove(key)
            self._last_hit = False
            return None

        self._last_hit = True
        return self._deserialize(row["results"])

    def put(self, key: str, results: list[SearchResult]) -> None:
        #serializes and stores the results under the given cache key
        sql = """
            INSERT INTO cache_results (cache_key, results, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                results = excluded.results,
                created_at = excluded.created_at
        """
        try:
            with get_connection(self._db_path) as conn:
                conn.execute(sql, (key, self._serialize(results), time.time()))
        except Exception:
            pass

    def invalidate(self) -> None:
        #clears all cached entries
        try:
            with get_connection(self._db_path) as conn:
                conn.execute("DELETE FROM cache_results")
        except Exception:
            pass

    def get_last_hit(self) -> bool:
        #returns True if the most recent get() call was a cache hit
        return self._last_hit

    #deletes one entry
    def _remove(self, key: str) -> None:
        try:
            with get_connection(self._db_path) as conn:
                conn.execute("DELETE FROM cache_results WHERE cache_key = ?", (key,))
        except Exception:
            pass

    def _serialize(self, results: list[SearchResult]) -> str:
        return json.dumps([
            {
                "path": r.path,
                "filename": r.filename,
                "preview": r.preview,
                "modified_at": r.modified_at,
                "score": r.score,
            }
            for r in results
        ])

    def _deserialize(self, data: str) -> list[SearchResult]:
        return [
            SearchResult(
                path=item["path"],
                filename=item["filename"],
                preview=item["preview"],
                modified_at=item["modified_at"],
                score=item["score"],
            )
            for item in json.loads(data)
        ]




"""Theoretically a Proxy design works as both proxy class and the 'Real_Implementation class' inherit from the same interface
as QueryEngine does not implement an interface either will CachedQueryEngine(which is the proxy class)
Simply just inject the real QueryEngine into the CachedQuery class and then delegate wether the search() method
will perform a cached search or a normal flow search"""
class CachedQueryEngine:
    #proxy that wraps a QueryEngine intercepting search() to check the disk cache first

    def __init__(self, engine: QueryEngine, cache: SearchCache):
        self._engine = engine # hold a refference to the real QueryEngine and delegate to it when needed
        self._cache = cache

    #the normal search is replaced now, but we still need to notify any obserevers
    #and the History tracking tracks the correct counts in a correct way
    def search(self, raw_query: str) -> list[SearchResult]:
        #notify observers on every call so history tracking stays accurate
        for observer in self._engine._observers:
            observer.on_search(raw_query)

        cache_key = self._build_key(raw_query)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        #cache miss -> delegate to the real engine but skip observer notifications since we already notified above
        results = self._engine._execute_search(raw_query)

        self._cache.put(cache_key, results)
        return results

    #method that build the raw_query_str :: strategy
    def _build_key(self, raw_query: str) -> str:
        #combines normalized query text with the ranking strategy name
        normalized = raw_query.strip().lower()
        strategy = self._engine.strategy_name()
        return f"{normalized}::{strategy}"
