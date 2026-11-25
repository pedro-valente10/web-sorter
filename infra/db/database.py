"""Acesso ao SQLite: conexões curtas, uma por operação."""
import sqlite3
from contextlib import contextmanager
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sorting_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (user_id, folder_name)
);

CREATE TABLE IF NOT EXISTS destinations (
    session_id INTEGER NOT NULL
        REFERENCES sorting_sessions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (session_id, name)
);

CREATE TABLE IF NOT EXISTS file_decisions (
    session_id INTEGER NOT NULL
        REFERENCES sorting_sessions(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    action TEXT NOT NULL,
    destination TEXT,
    applied INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, path)
);

CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    sources TEXT NOT NULL,
    destination TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS batch_items (
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    source INTEGER NOT NULL,
    name TEXT NOT NULL,
    target_name TEXT,
    status TEXT NOT NULL,
    error TEXT,
    PRIMARY KEY (batch_id, position)
);
"""


class Database:
    def __init__(self, path: str):
        self._path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA)
