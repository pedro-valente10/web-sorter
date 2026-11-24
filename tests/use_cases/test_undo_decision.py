import pytest

from domain.errors import NotFoundError, ValidationError
from use_cases.mark_decision_applied import MarkDecisionApplied
from use_cases.record_decision import RecordDecision
from use_cases.undo_decision import UndoDecision


@pytest.fixture
def undo(sessions, decisions, clock):
    return UndoDecision(sessions, decisions, clock)


@pytest.fixture
def record(sessions, decisions, clock):
    return RecordDecision(sessions, decisions, clock)


def test_removes_existing_decision(undo, record, session, decisions):
    record.execute(1, session.id, "a.jpg", "delete")
    assert undo.execute(1, session.id, "a.jpg") is True
    assert decisions.get(session.id, "a.jpg") is None


def test_is_idempotent_when_there_is_no_decision(undo, session):
    assert undo.execute(1, session.id, "a.jpg") is False


def test_applied_decision_cannot_be_undone(
    undo, record, session, sessions, decisions, clock
):
    record.execute(1, session.id, "a.jpg", "delete")
    MarkDecisionApplied(sessions, decisions, clock).execute(
        1, session.id, "a.jpg"
    )
    with pytest.raises(ValidationError):
        undo.execute(1, session.id, "a.jpg")
    assert decisions.get(session.id, "a.jpg") is not None


def test_cannot_undo_on_another_users_session(
    undo, record, session, decisions
):
    record.execute(1, session.id, "a.jpg", "delete")
    with pytest.raises(NotFoundError):
        undo.execute(2, session.id, "a.jpg")
    assert decisions.get(session.id, "a.jpg") is not None
