"""História 4: decidir o que fazer com um arquivo (mover/excluir/manter)."""
from domain.errors import ValidationError
from domain.file_decision import Action, FileDecision
from use_cases.ports import (
    Clock,
    DecisionRepository,
    SessionRepository,
    utc_now,
)
from use_cases.session_access import get_owned_session


class RecordDecision:
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
        self,
        user_id: int,
        session_id: int,
        path: str,
        action: str,
        destination: str | None = None,
    ) -> FileDecision:
        session = get_owned_session(self._sessions, session_id, user_id)
        parsed = Action.parse(action)
        if parsed is Action.MOVE:
            destination = session.find_destination(destination)
            if destination is None:
                raise ValidationError("Destino não cadastrado.")
        decision = FileDecision(
            session_id=session.id,
            path=path,
            action=parsed,
            destination=destination,
        )
        self._decisions.save(decision)
        session.touch(self._clock())
        self._sessions.update(session)
        return decision
