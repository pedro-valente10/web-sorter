"""História 4 (parte): registrar que a decisão foi executada na pasta."""
from domain.errors import NotFoundError
from domain.file_decision import FileDecision
from use_cases.ports import (
    Clock,
    DecisionRepository,
    SessionRepository,
    utc_now,
)
from use_cases.session_access import get_owned_session


class MarkDecisionApplied:
    def __init__(
        self,
        sessions: SessionRepository,
        decisions: DecisionRepository,
        clock: Clock = utc_now,
    ):
        self._sessions = sessions
        self._decisions = decisions
        self._clock = clock

    def execute(
        self, user_id: int, session_id: int, path: str
    ) -> FileDecision:
        session = get_owned_session(self._sessions, session_id, user_id)
        decision = self._decisions.get(session.id, path)
        if decision is None:
            raise NotFoundError("Decisão não encontrada.")
        applied = decision.mark_applied()
        self._decisions.save(applied)
        session.touch(self._clock())
        self._sessions.update(session)
        return applied
