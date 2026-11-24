"""Testes de integração leves: repositórios reais sobre SQLite em disco."""
import pytest

from domain.errors import UsernameAlreadyExistsError
from domain.file_decision import Action, FileDecision
from domain.sorting_session import SortingSession
from domain.user import User
from infra.db.database import Database
from infra.repositories.decision_repository_sqlite import (
    SqliteDecisionRepository,
)
from infra.repositories.session_repository_sqlite import (
    SqliteSessionRepository,
)
from infra.repositories.user_repository_sqlite import SqliteUserRepository
from tests.fakes import FakeClock


@pytest.fixture
def database(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    return db


def test_user_roundtrip_and_unique_username(database):
    repo = SqliteUserRepository(database)
    saved = repo.add(User(None, "ana", "hash"))
    assert repo.find_by_username("ana") == saved
    assert repo.find_by_username("outra") is None
    with pytest.raises(UsernameAlreadyExistsError):
        repo.add(User(None, "ana", "hash2"))


def test_session_keeps_destinations_in_order(database):
    users = SqliteUserRepository(database)
    sessions = SqliteSessionRepository(database)
    user = users.add(User(None, "ana", "hash"))
    now = FakeClock()()
    session = sessions.add(
        SortingSession(
            user_id=user.id, folder_name="Fotos",
            created_at=now, updated_at=now,
        )
    )
    session.add_destination("Zebra")
    session.add_destination("Abelha")
    sessions.update(session)

    loaded = sessions.find_by_user_and_folder(user.id, "Fotos")

    assert loaded.id == session.id
    assert loaded.destinations == ["Zebra", "Abelha"]
    assert loaded.updated_at == now
    assert sessions.list_by_user(user.id)[0].id == session.id


def test_decision_upsert_get_delete(database):
    users = SqliteUserRepository(database)
    sessions = SqliteSessionRepository(database)
    decisions = SqliteDecisionRepository(database)
    user = users.add(User(None, "ana", "hash"))
    now = FakeClock()()
    session = sessions.add(
        SortingSession(
            user_id=user.id, folder_name="Fotos",
            created_at=now, updated_at=now,
        )
    )

    decisions.save(FileDecision(session.id, "a.jpg", Action.DELETE))
    decisions.save(FileDecision(session.id, "a.jpg", Action.KEEP))
    decisions.save(
        FileDecision(session.id, "b.jpg", Action.KEEP).mark_applied()
    )

    stored = decisions.list_by_session(session.id)
    assert [(d.path, d.action, d.applied) for d in stored] == [
        ("a.jpg", Action.KEEP, False),
        ("b.jpg", Action.KEEP, True),
    ]
    assert decisions.delete(session.id, "a.jpg") is True
    assert decisions.delete(session.id, "a.jpg") is False
    assert decisions.get(session.id, "a.jpg") is None
