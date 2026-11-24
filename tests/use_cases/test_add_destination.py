import pytest

from domain.errors import NotFoundError, ValidationError
from use_cases.add_destination import AddDestination


@pytest.fixture
def add_destination(sessions, clock):
    return AddDestination(sessions, clock)


def test_adds_destination_and_updates_activity(
    add_destination, session, sessions
):
    before = session.updated_at
    updated = add_destination.execute(1, session.id, " Viagem ")
    assert updated.destinations == ["Viagem"]
    assert sessions.get(session.id).updated_at > before


def test_rejects_duplicate(add_destination, session):
    add_destination.execute(1, session.id, "Viagem")
    with pytest.raises(ValidationError):
        add_destination.execute(1, session.id, "viagem")


def test_cannot_change_another_users_session(add_destination, session):
    with pytest.raises(NotFoundError):
        add_destination.execute(2, session.id, "Viagem")


def test_unknown_session(add_destination):
    with pytest.raises(NotFoundError):
        add_destination.execute(1, 999, "Viagem")
