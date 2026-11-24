"""História 3: abrir uma pasta e retomar de onde parou."""
from dataclasses import dataclass

from domain.file_decision import FileDecision
from domain.sorting_session import SortingSession, normalize_folder_name
from use_cases.ports import Clock, DecisionRepository, SessionRepository
from use_cases.ports import utc_now


@dataclass(frozen=True)
class SessionState:
    session: SortingSession
    decisions: list[FileDecision]


class OpenSession:
    def __init__(
        self,
        sessions: SessionRepository,
        decisions: DecisionRepository,
        clock: Clock = utc_now,
    ):
        self._sessions = sessions
        self._decisions = decisions
        self._clock = clock

    def execute(self, user_id: int, folder_name: str) -> SessionState:
        name = normalize_folder_name(folder_name)
        now = self._clock()
        session = self._sessions.find_by_user_and_folder(user_id, name)
        if session is None:
            session = self._sessions.add(
                SortingSession(
                    user_id=user_id,
                    folder_name=name,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            session.touch(now)
            self._sessions.update(session)
        return SessionState(
            session=session,
            decisions=self._decisions.list_by_session(session.id),
        )
