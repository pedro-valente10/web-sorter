import pytest

from domain.errors import NotFoundError
from use_cases.mark_decision_applied import MarkDecisionApplied
from use_cases.record_decision import RecordDecision


@pytest.fixture
def mark_applied(sessions, decisions, clock):
    return MarkDecisionApplied(sessions, decisions, clock)


def test_marks_decision_as_applied_and_persists(
    mark_applied, session, sessions, decisions, clock
):
    RecordDecision(sessions, decisions, clock).execute(
        1, session.id, "a.jpg", "delete"
    )
    result = mark_applied.execute(1, session.id, "a.jpg")
    assert result.applied is True
    assert decisions.get(session.id, "a.jpg").applied is True


def test_missing_decision(mark_applied, session):
    with pytest.raises(NotFoundError):
        mark_applied.execute(1, session.id, "a.jpg")


def test_other_users_session_is_not_found(mark_applied, session):
    with pytest.raises(NotFoundError):
        mark_applied.execute(2, session.id, "a.jpg")
