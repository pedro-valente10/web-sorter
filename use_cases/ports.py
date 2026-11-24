"""Portas (interfaces) que os casos de uso exigem da infraestrutura.

Os casos de uso dependem apenas destas abstrações (Inversão de Dependência).
Cada porta é pequena e específica (Segregação de Interfaces).
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable

from domain.file_decision import FileDecision
from domain.sorting_session import SortingSession
from domain.user import User

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User:
        """Persiste o usuário e devolve-o com o id preenchido."""

    @abstractmethod
    def find_by_username(self, username: str) -> User | None:
        ...


class SessionRepository(ABC):
    @abstractmethod
    def add(self, session: SortingSession) -> SortingSession:
        ...

    @abstractmethod
    def get(self, session_id: int) -> SortingSession | None:
        ...

    @abstractmethod
    def find_by_user_and_folder(
        self, user_id: int, folder_name: str
    ) -> SortingSession | None:
        ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[SortingSession]:
        ...

    @abstractmethod
    def update(self, session: SortingSession) -> None:
        ...


class DecisionRepository(ABC):
    @abstractmethod
    def save(self, decision: FileDecision) -> None:
        """Insere ou substitui a decisão do mesmo (sessão, caminho)."""

    @abstractmethod
    def get(self, session_id: int, path: str) -> FileDecision | None:
        ...

    @abstractmethod
    def delete(self, session_id: int, path: str) -> bool:
        ...

    @abstractmethod
    def list_by_session(self, session_id: int) -> list[FileDecision]:
        ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        ...
