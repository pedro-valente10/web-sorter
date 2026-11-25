"""BatchItemRepository sobre SQLite."""
import sqlite3

from domain.batch import BatchItem, BatchProgress, ItemStatus
from infra.db.database import Database
from use_cases.ports import BatchItemRepository

_COLUMNS = "batch_id, position, source, name, target_name, status, error"


class SqliteBatchItemRepository(BatchItemRepository):
    def __init__(self, database: Database):
        self._db = database

    def get(self, batch_id: int, position: int) -> BatchItem | None:
        with self._db.connection() as conn:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM batch_items "
                "WHERE batch_id = ? AND position = ?",
                (batch_id, position),
            ).fetchone()
        return None if row is None else self._to_entity(row)

    def list_by_batch(self, batch_id: int) -> list[BatchItem]:
        with self._db.connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM batch_items "
                "WHERE batch_id = ? ORDER BY position",
                (batch_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def save_all(self, items: list[BatchItem]) -> None:
        with self._db.connection() as conn:
            conn.executemany(
                "UPDATE batch_items SET target_name = ?, status = ?, "
                "error = ? WHERE batch_id = ? AND position = ?",
                [
                    (
                        item.target_name,
                        item.status.value,
                        item.error,
                        item.batch_id,
                        item.position,
                    )
                    for item in items
                ],
            )

    def progress(self, batch_id: int) -> BatchProgress:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS amount FROM batch_items "
                "WHERE batch_id = ? GROUP BY status",
                (batch_id,),
            ).fetchall()
        amounts = {row["status"]: row["amount"] for row in rows}
        return BatchProgress(
            total=sum(amounts.values()),
            done=amounts.get(ItemStatus.DONE.value, 0),
            failed=amounts.get(ItemStatus.FAILED.value, 0),
        )

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> BatchItem:
        return BatchItem(
            batch_id=row["batch_id"],
            position=row["position"],
            source=row["source"],
            name=row["name"],
            target_name=row["target_name"],
            status=ItemStatus(row["status"]),
            error=row["error"],
        )
