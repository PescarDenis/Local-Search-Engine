from .connection import get_connection


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
    content     TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    filename,
    content,
    content='files',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS files_ai
AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, filename, content)
    VALUES (new.id, new.filename, new.content);
END;

CREATE TRIGGER IF NOT EXISTS files_ad
AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, filename, content)
    VALUES ('delete', old.id, old.filename, old.content);
END;

CREATE TRIGGER IF NOT EXISTS files_au
AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, filename, content)
    VALUES ('delete', old.id, old.filename, old.content);
    INSERT INTO files_fts(rowid, filename, content)
    VALUES (new.id, new.filename, new.content);
END;
"""


def initialise(db_path: str) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(_SCHEMA)
