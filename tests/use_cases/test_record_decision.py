import pytest

from domain.errors import NotFoundError, ValidationError
from domain.file_decision import Action
from use_cases.record_decision import RecordDecision


@pytest.fixture
def record(sessions, decisions, clock):
    return RecordDecision(sessions, decisions, clock)


@pytest.fixture
def with_destination(session, sessions):
    session.add_destination("Viagem")
    sessions.update(session)
    return session


def test_records_move_using_canonical_destination_name(
    record, with_destination, decisions
):
    decision = record.execute(
        1, with_destination.id, "a.jpg", "move", " VIAGEM "
    )
    assert decision.action is Action.MOVE
    assert decision.destination == "Viagem"
    assert decisions.get(with_destination.id, "a.jpg") == decision


def test_move_to_unregistered_destination_is_rejected(
    record, session, decisions
):
    with pytest.raises(ValidationError):
        record.execute(1, session.id, "a.jpg", "move", "Inexistente")
    assert decisions.list_by_session(session.id) == []


@pytest.mark.parametrize("action", ["delete", "keep"])
def test_records_delete_and_keep(record, session, action):
    decision = record.execute(1, session.id, "a.jpg", action)
    assert decision.action.value == action
    assert decision.destination is None


def test_new_decision_replaces_previous_one(record, session, decisions):
    record.execute(1, session.id, "a.jpg", "delete")
    record.execute(1, session.id, "a.jpg", "keep")
    saved = decisions.list_by_session(session.id)
    assert [d.action for d in saved] == [Action.KEEP]


def test_rejects_unknown_action(record, session):
    with pytest.raises(ValidationError):
        record.execute(1, session.id, "a.jpg", "queimar")


def test_cannot_record_on_another_users_session(
    record, session, decisions
):
    with pytest.raises(NotFoundError):
        record.execute(2, session.id, "a.jpg", "delete")
    assert decisions.list_by_session(session.id) == []
