import pytest

from tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    InMemoryDecisionRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
)
from use_cases.open_session import OpenSession


@pytest.fixture
def users():
    return InMemoryUserRepository()


@pytest.fixture
def sessions():
    return InMemorySessionRepository()


@pytest.fixture
def decisions():
    return InMemoryDecisionRepository()


@pytest.fixture
def hasher():
    return FakePasswordHasher()


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def open_session(sessions, decisions, clock):
    return OpenSession(sessions, decisions, clock)


@pytest.fixture
def session(open_session):
    """Sessão do usuário 1 na pasta 'Fotos', já criada."""
    return open_session.execute(1, "Fotos").session
