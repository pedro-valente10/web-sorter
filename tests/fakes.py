"""Dublês em memória das portas: testam os casos de uso sem infraestrutura."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from domain.errors import UsernameAlreadyExistsError
from domain.file_decision import FileDecision
from domain.sorting_session import SortingSession
from domain.user import User
from use_cases.ports import (
    DecisionRepository,
    PasswordHasher,
    SessionRepository,
    UserRepository,
)


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self.users: dict[str, User] = {}

    def add(self, user: User) -> User:
        if user.username in self.users:
            raise UsernameAlreadyExistsError("duplicado")
        stored = replace(user, id=len(self.users) + 1)
        self.users[user.username] = stored
        return stored

    def find_by_username(self, username: str) -> User | None:
        return self.users.get(username)


class InMemorySessionRepository(SessionRepository):
    def __init__(self):
        self.sessions: dict[int, SortingSession] = {}

    def add(self, session: SortingSession) -> SortingSession:
        session.id = len(self.sessions) + 1
        self.sessions[session.id] = session
        return session

    def get(self, session_id: int) -> SortingSession | None:
        return self.sessions.get(session_id)

    def find_by_user_and_folder(self, user_id, folder_name):
        for session in self.sessions.values():
            if (session.user_id, session.folder_name) == (
                user_id, folder_name
            ):
                return session
        return None

    def list_by_user(self, user_id: int) -> list[SortingSession]:
        return [s for s in self.sessions.values() if s.user_id == user_id]

    def update(self, session: SortingSession) -> None:
        self.sessions[session.id] = session


class InMemoryDecisionRepository(DecisionRepository):
    def __init__(self):
        self.items: dict[tuple[int, str], FileDecision] = {}

    def save(self, decision: FileDecision) -> None:
        self.items[(decision.session_id, decision.path)] = decision

    def get(self, session_id: int, path: str) -> FileDecision | None:
        return self.items.get((session_id, path))

    def delete(self, session_id: int, path: str) -> bool:
        return self.items.pop((session_id, path), None) is not None

    def list_by_session(self, session_id: int) -> list[FileDecision]:
        return [d for (sid, _), d in self.items.items() if sid == session_id]


class FakeClock:
    """Relógio controlável: cada chamada avança um minuto."""

    def __init__(self):
        self._now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self._now
        self._now += timedelta(minutes=1)
        return current
