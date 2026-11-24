"""SessionRepository sobre SQLite (sessão + seus destinos)."""
import sqlite3
from datetime import datetime

from domain.sorting_session import SortingSession
from infra.db.database import Database
from use_cases.ports import SessionRepository

_COLUMNS = "id, user_id, folder_name, created_at, updated_at"


class SqliteSessionRepository(SessionRepository):
    def __init__(self, database: Database):
        self._db = database

    def add(self, session: SortingSession) -> SortingSession:
        with self._db.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO sorting_sessions "
                "(user_id, folder_name, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    session.user_id,
                    session.folder_name,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                ),
            )
            session.id = cursor.lastrowid
            self._replace_destinations(conn, session)
        return session

    def get(self, session_id: int) -> SortingSession | None:
        with self._db.connection() as conn:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM sorting_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            return self._hydrate(conn, row)

    def find_by_user_and_folder(
        self, user_id: int, folder_name: str
    ) -> SortingSession | None:
        with self._db.connection() as conn:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM sorting_sessions "
                "WHERE user_id = ? AND folder_name = ?",
                (user_id, folder_name),
            ).fetchone()
            return self._hydrate(conn, row)

    def list_by_user(self, user_id: int) -> list[SortingSession]:
        with self._db.connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM sorting_sessions "
                "WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
            return [self._hydrate(conn, row) for row in rows]

    def update(self, session: SortingSession) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE sorting_sessions SET updated_at = ? WHERE id = ?",
                (session.updated_at.isoformat(), session.id),
            )
            self._replace_destinations(conn, session)

    @staticmethod
    def _replace_destinations(
        conn: sqlite3.Connection, session: SortingSession
    ) -> None:
        conn.execute(
            "DELETE FROM destinations WHERE session_id = ?", (session.id,)
        )
        conn.executemany(
            "INSERT INTO destinations (session_id, name, position) "
            "VALUES (?, ?, ?)",
            [
                (session.id, name, position)
                for position, name in enumerate(session.destinations)
            ],
        )

    @staticmethod
    def _hydrate(
        conn: sqlite3.Connection, row: sqlite3.Row | None
    ) -> SortingSession | None:
        if row is None:
            return None
        names = conn.execute(
            "SELECT name FROM destinations WHERE session_id = ? "
            "ORDER BY position",
            (row["id"],),
        ).fetchall()
        return SortingSession(
            id=row["id"],
            user_id=row["user_id"],
            folder_name=row["folder_name"],
            destinations=[item["name"] for item in names],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
