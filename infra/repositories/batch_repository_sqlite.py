"""BatchRepository sobre SQLite."""
import json
import sqlite3
from dataclasses import replace
from datetime import datetime

from domain.batch import Batch, BatchItem, BatchKind, BatchStatus
from infra.db.database import Database
from use_cases.ports import BatchRepository

_COLUMNS = (
    "id, user_id, kind, sources, destination, status, "
    "created_at, finished_at"
)


class SqliteBatchRepository(BatchRepository):
    def __init__(self, database: Database):
        self._db = database

    def add(
        self, batch: Batch, items: list[BatchItem]
    ) -> tuple[Batch, list[BatchItem]]:
        with self._db.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO batches (user_id, kind, sources, destination, "
                "status, created_at, finished_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    batch.user_id,
                    batch.kind.value,
                    json.dumps(batch.sources, ensure_ascii=False),
                    batch.destination,
                    batch.status.value,
                    batch.created_at.isoformat(),
                    _iso(batch.finished_at),
                ),
            )
            batch.id = cursor.lastrowid
            stored = [replace(item, batch_id=batch.id) for item in items]
            conn.executemany(
                "INSERT INTO batch_items (batch_id, position, source, "
                "name, target_name, status, error) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        item.batch_id,
                        item.position,
                        item.source,
                        item.name,
                        item.target_name,
                        item.status.value,
                        item.error,
                    )
                    for item in stored
                ],
            )
        return batch, stored

    def get(self, batch_id: int) -> Batch | None:
        with self._db.connection() as conn:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM batches WHERE id = ?", (batch_id,)
            ).fetchone()
        return None if row is None else self._to_entity(row)

    def list_by_user(self, user_id: int) -> list[Batch]:
        with self._db.connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM batches WHERE user_id = ? "
                "ORDER BY created_at DESC, id DESC",
                (user_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def update(self, batch: Batch) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE batches SET status = ?, finished_at = ? "
                "WHERE id = ?",
                (batch.status.value, _iso(batch.finished_at), batch.id),
            )

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> Batch:
        finished_at = row["finished_at"]
        return Batch(
            id=row["id"],
            user_id=row["user_id"],
            kind=BatchKind(row["kind"]),
            sources=tuple(json.loads(row["sources"])),
            destination=row["destination"],
            status=BatchStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            finished_at=(
                datetime.fromisoformat(finished_at) if finished_at else None
            ),
        )


def _iso(when: datetime | None) -> str | None:
    return None if when is None else when.isoformat()
