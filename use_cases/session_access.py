"""Regra compartilhada: só o dono enxerga e altera a própria sessão."""
from domain.errors import NotFoundError
from domain.sorting_session import SortingSession
from use_cases.ports import SessionRepository


def get_owned_session(
    sessions: SessionRepository, session_id: int, user_id: int
) -> SortingSession:
    session = sessions.get(session_id)
    if session is None or session.user_id != user_id:
        # Mesma resposta nos dois casos para não revelar que a sessão existe.
        raise NotFoundError("Sessão não encontrada.")
    return session
