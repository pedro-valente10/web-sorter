import pytest

from domain.errors import NotFoundError
from use_cases.get_session_summary import GetSessionSummary
from use_cases.mark_decision_applied import MarkDecisionApplied
from use_cases.record_decision import RecordDecision


@pytest.fixture
def summary(sessions, decisions):
    return GetSessionSummary(sessions, decisions)


def test_empty_session_has_zeroed_counters(summary, session):
    result = summary.execute(1, session.id)
    assert result.total == 0
    assert result.applied == 0
    assert result.by_action == {"move": 0, "delete": 0, "keep": 0}
    assert result.by_destination == {}


def test_counts_by_action_destination_and_applied(
    summary, session, sessions, decisions, clock
):
    session.add_destination("Viagem")
    sessions.update(session)
    record = RecordDecision(sessions, decisions, clock)
    record.execute(1, session.id, "a.jpg", "move", "Viagem")
    record.execute(1, session.id, "b.jpg", "move", "Viagem")
    record.execute(1, session.id, "c.jpg", "delete")
    record.execute(1, session.id, "d.jpg", "keep")
    MarkDecisionApplied(sessions, decisions, clock).execute(
        1, session.id, "c.jpg"
    )

    result = summary.execute(1, session.id)

    assert result.total == 4
    assert result.applied == 1
    assert result.pending == 3
    assert result.by_action == {"move": 2, "delete": 1, "keep": 1}
    assert result.by_destination == {"Viagem": 2}


def test_other_users_session_is_not_found(summary, session):
    with pytest.raises(NotFoundError):
        summary.execute(2, session.id)
