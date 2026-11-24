"""História 4 (parte): desfazer uma decisão ainda não aplicada."""
from domain.errors import ValidationError
from use_cases.ports import (
    Clock,
    DecisionRepository,
    SessionRepository,
    utc_now,
)
from use_cases.session_access import get_owned_session


class UndoDecision:
    def __init__(
        self,
        sessions: SessionRepository,
        decisions: DecisionRepository,
        clock: Clock = utc_now,
    ):
        self._sessions = sessions
        self._decisions = decisions
        self._clock = clock

    def execute(self, user_id: int, session_id: int, path: str) -> bool:
        """Devolve True se havia decisão para remover (idempotente)."""
        session = get_owned_session(self._sessions, session_id, user_id)
        current = self._decisions.get(session.id, path)
        if current is None:
            return False
        if current.applied:
            raise ValidationError(
                "Decisão já aplicada na pasta não pode ser desfeita."
            )
        removed = self._decisions.delete(session.id, current.path)
        session.touch(self._clock())
        self._sessions.update(session)
        return removed
