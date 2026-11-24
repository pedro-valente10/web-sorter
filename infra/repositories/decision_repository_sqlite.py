"""DecisionRepository sobre SQLite."""
import sqlite3

from domain.file_decision import Action, FileDecision
from infra.db.database import Database
from use_cases.ports import DecisionRepository

_COLUMNS = "session_id, path, action, destination, applied"


class SqliteDecisionRepository(DecisionRepository):
    def __init__(self, database: Database):
        self._db = database

    def save(self, decision: FileDecision) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "INSERT INTO file_decisions "
                "(session_id, path, action, destination, applied) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (session_id, path) DO UPDATE SET "
                "action = excluded.action, "
                "destination = excluded.destination, "
                "applied = excluded.applied",
                (
                    decision.session_id,
                    decision.path,
                    decision.action.value,
                    decision.destination,
                    int(decision.applied),
                ),
            )

    def get(self, session_id: int, path: str) -> FileDecision | None:
        with self._db.connection() as conn:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM file_decisions "
                "WHERE session_id = ? AND path = ?",
                (session_id, path),
            ).fetchone()
        return None if row is None else self._to_entity(row)

    def delete(self, session_id: int, path: str) -> bool:
        with self._db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM file_decisions "
                "WHERE session_id = ? AND path = ?",
                (session_id, path),
            )
        return cursor.rowcount > 0

    def list_by_session(self, session_id: int) -> list[FileDecision]:
        with self._db.connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM file_decisions "
                "WHERE session_id = ? ORDER BY path",
                (session_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> FileDecision:
        return FileDecision(
            session_id=row["session_id"],
            path=row["path"],
            action=Action(row["action"]),
            destination=row["destination"],
            applied=bool(row["applied"]),
        )
