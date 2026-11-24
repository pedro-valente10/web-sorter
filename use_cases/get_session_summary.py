"""História 5: acompanhar o progresso da organização."""
from collections import Counter
from dataclasses import dataclass

from domain.file_decision import Action
from use_cases.ports import DecisionRepository, SessionRepository
from use_cases.session_access import get_owned_session


@dataclass(frozen=True)
class SessionSummary:
    total: int
    applied: int
    pending: int
    by_action: dict[str, int]
    by_destination: dict[str, int]


class GetSessionSummary:
    def __init__(
        self, sessions: SessionRepository, decisions: DecisionRepository
    ):
        self._sessions = sessions
        self._decisions = decisions

    def execute(self, user_id: int, session_id: int) -> SessionSummary:
        session = get_owned_session(self._sessions, session_id, user_id)
        decisions = self._decisions.list_by_session(session.id)
        by_action = Counter({action.value: 0 for action in Action})
        by_action.update(d.action.value for d in decisions)
        by_destination = Counter(
            d.destination for d in decisions if d.destination
        )
        applied = sum(1 for d in decisions if d.applied)
        return SessionSummary(
            total=len(decisions),
            applied=applied,
            pending=len(decisions) - applied,
            by_action=dict(by_action),
            by_destination=dict(by_destination),
        )
