"""Raiz de composição: único lugar que conhece as implementações concretas."""
from dataclasses import dataclass

from flask import current_app

from infra.db.database import Database
from infra.repositories.decision_repository_sqlite import (
    SqliteDecisionRepository,
)
from infra.repositories.session_repository_sqlite import (
    SqliteSessionRepository,
)
from infra.repositories.user_repository_sqlite import SqliteUserRepository
from infra.security.password_hasher_werkzeug import WerkzeugPasswordHasher
from use_cases.add_destination import AddDestination
from use_cases.authenticate_user import AuthenticateUser
from use_cases.get_session_summary import GetSessionSummary
from use_cases.list_sessions import ListSessions
from use_cases.mark_decision_applied import MarkDecisionApplied
from use_cases.open_session import OpenSession
from use_cases.record_decision import RecordDecision
from use_cases.register_user import RegisterUser
from use_cases.undo_decision import UndoDecision


@dataclass(frozen=True)
class Container:
    register_user: RegisterUser
    authenticate_user: AuthenticateUser
    list_sessions: ListSessions
    open_session: OpenSession
    add_destination: AddDestination
    record_decision: RecordDecision
    undo_decision: UndoDecision
    mark_decision_applied: MarkDecisionApplied
    get_session_summary: GetSessionSummary


def build_container(database: Database) -> Container:
    users = SqliteUserRepository(database)
    sessions = SqliteSessionRepository(database)
    decisions = SqliteDecisionRepository(database)
    hasher = WerkzeugPasswordHasher()
    return Container(
        register_user=RegisterUser(users, hasher),
        authenticate_user=AuthenticateUser(users, hasher),
        list_sessions=ListSessions(sessions),
        open_session=OpenSession(sessions, decisions),
        add_destination=AddDestination(sessions),
        record_decision=RecordDecision(sessions, decisions),
        undo_decision=UndoDecision(sessions, decisions),
        mark_decision_applied=MarkDecisionApplied(sessions, decisions),
        get_session_summary=GetSessionSummary(sessions, decisions),
    )


def get_container() -> Container:
    return current_app.extensions["container"]
