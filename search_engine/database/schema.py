from .connection import get_connection

"""Add the path to the FTS table"""
"""Cache Results creates the table for caching with persistence on disk as we don t have an interactive CLI, entries:
 -cache key -> it is a string in form of a raw query :: sorting strategy
 -results -> used for serializing and deserializing results of the cache in form of a json file, the data object is the same SearchResult
 -created_at -> timestamp that records when a cache entry was stored and it is used for Time to Live expiration to prevent getting 
 outdated results
 """
_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY,
    path        TEXT UNIQUE NOT NULL,
    filename    TEXT NOT NULL,
    extension   TEXT,
    size_bytes  INTEGER,
    mime_type   TEXT,
    created_at  REAL,
    modified_at REAL,
    preview     TEXT,
    content     TEXT,
    weight      REAL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY,
    query TEXT UNIQUE NOT NULL,
    search_count INTEGER DEFAULT 1,
    timestamp REAL
);
CREATE TABLE IF NOT EXISTS cache_results (
    cache_key   TEXT PRIMARY KEY,
    results     TEXT NOT NULL,
    created_at  REAL NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    path,
    filename,
    content,
    content='files',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS files_ai
AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, path, filename, content)
    VALUES (new.id, new.path, new.filename, new.content);
END;

CREATE TRIGGER IF NOT EXISTS files_ad
AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, path, filename, content)
    VALUES ('delete', old.id, old.path, old.filename, old.content);
END;

CREATE TRIGGER IF NOT EXISTS files_au
AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, path, filename, content)
    VALUES ('delete', old.id, old.path, old.filename, old.content);
    INSERT INTO files_fts(rowid, path, filename, content)
    VALUES (new.id, new.path, new.filename, new.content);
END;
"""


def initialise(db_path: str) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(_SCHEMA)
