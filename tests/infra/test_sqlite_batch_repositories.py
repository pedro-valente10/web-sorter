"""Repositórios de lote sobre SQLite em disco."""
import pytest

from domain.batch import Batch, BatchKind, BatchProgress, FileRef
from domain.user import User
from infra.db.database import Database
from infra.repositories.batch_item_repository_sqlite import (
    SqliteBatchItemRepository,
)
from infra.repositories.batch_repository_sqlite import SqliteBatchRepository
from infra.repositories.user_repository_sqlite import SqliteUserRepository
from tests.fakes import FakeClock


@pytest.fixture
def database(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    return db


@pytest.fixture
def user(database):
    return SqliteUserRepository(database).add(User(None, "ana", "hash"))


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def store(database, user, clock):
    def _store(**changes):
        values = {
            "kind": BatchKind.MOVE,
            "sources": ("Férias", "Fotos/2025"),
            "destination": "Praia",
        }
        values.update(changes)
        batch = Batch(user_id=user.id, created_at=clock(), **values)
        files = [FileRef(0, "a.jpg"), FileRef(1, "a.jpg")]
        items = batch.plan(files, [])
        return SqliteBatchRepository(database).add(batch, items)
    return _store


def test_batch_roundtrip(database, store):
    batch, _ = store()
    assert SqliteBatchRepository(database).get(batch.id) == batch


def test_items_roundtrip(database, store):
    batch, items = store()
    repo = SqliteBatchItemRepository(database)
    assert repo.list_by_batch(batch.id) == items
    assert repo.get(batch.id, 1) == items[1]
    assert items[1].target_name == "a (1).jpg"
    assert repo.get(batch.id, 2) is None


def test_progress_follows_results(database, store):
    batch, items = store()
    repo = SqliteBatchItemRepository(database)
    repo.save_all([items[0].succeed(), items[1].fail("motivo")])
    assert repo.progress(batch.id) == BatchProgress(2, 1, 1)
    assert repo.get(batch.id, 1).error == "motivo"


def test_update_keeps_the_closing_date(database, store, clock):
    batch, _ = store()
    batch.interrupt(clock())
    repo = SqliteBatchRepository(database)
    repo.update(batch)
    assert repo.get(batch.id) == batch


def test_list_is_per_user_and_newest_first(database, store, user):
    first, _ = store()
    second, _ = store(kind=BatchKind.DELETE, destination=None)
    repo = SqliteBatchRepository(database)
    assert [b.id for b in repo.list_by_user(user.id)] == [
        second.id, first.id,
    ]
    assert repo.list_by_user(user.id + 1) == []
    assert repo.get(999) is None


def test_old_databases_get_the_new_tables(tmp_path):
    db = Database(str(tmp_path / "antigo.db"))
    db.init_schema()
    with db.connection() as conn:
        conn.execute("DROP TABLE batch_items")
        conn.execute("DROP TABLE batches")
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES ('a', 'h')"
        )
    db.init_schema()
    assert SqliteBatchRepository(db).list_by_user(1) == []
    assert SqliteUserRepository(db).find_by_username("a") is not None
