import pytest

from domain.batch import FileRef
from tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    InMemoryBatchItemRepository,
    InMemoryBatchRepository,
    InMemoryDecisionRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
)
from use_cases.batch_request import BatchRequest
from use_cases.open_session import OpenSession
from use_cases.start_batch import StartBatch


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


@pytest.fixture
def batch_items():
    return InMemoryBatchItemRepository()


@pytest.fixture
def batches(batch_items):
    return InMemoryBatchRepository(batch_items)


@pytest.fixture
def start_batch(batches, clock):
    return StartBatch(batches, clock)


@pytest.fixture
def move_batch(start_batch):
    """Lote do usuário 1 movendo três fotos de 'Viagem' para 'Praia'."""
    return start_batch.execute(1, BatchRequest(
        kind="move",
        sources=("Fotos/Viagem",),
        destination="Fotos/Praia",
        files=tuple(FileRef(0, n) for n in ("a.jpg", "b.jpg", "c.jpg")),
    ))
