"""História 3 (parte): listar as pastas em que o usuário já trabalhou."""
from domain.sorting_session import SortingSession
from use_cases.ports import SessionRepository


class ListSessions:
    def __init__(self, sessions: SessionRepository):
        self._sessions = sessions

    def execute(self, user_id: int) -> list[SortingSession]:
        sessions = self._sessions.list_by_user(user_id)
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)
