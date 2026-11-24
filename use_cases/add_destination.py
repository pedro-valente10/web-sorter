"""História 4 (parte): cadastrar um destino para mover arquivos."""
from domain.sorting_session import SortingSession
from use_cases.ports import Clock, SessionRepository, utc_now
from use_cases.session_access import get_owned_session


class AddDestination:
    def __init__(self, sessions: SessionRepository, clock: Clock = utc_now):
        self._sessions = sessions
        self._clock = clock

    def execute(
        self, user_id: int, session_id: int, name: str
    ) -> SortingSession:
        session = get_owned_session(self._sessions, session_id, user_id)
        session.add_destination(name)
        session.touch(self._clock())
        self._sessions.update(session)
        return session
