"""Converte entidades e resultados de casos de uso em dicionários JSON."""
from domain.file_decision import FileDecision
from domain.sorting_session import SortingSession
from use_cases.get_session_summary import SessionSummary


def session_to_dict(session: SortingSession) -> dict:
    return {
        "id": session.id,
        "folder_name": session.folder_name,
        "destinations": list(session.destinations),
        "updated_at": session.updated_at.isoformat(),
    }


def decision_to_dict(decision: FileDecision) -> dict:
    return {
        "path": decision.path,
        "action": decision.action.value,
        "destination": decision.destination,
        "applied": decision.applied,
    }


def summary_to_dict(summary: SessionSummary) -> dict:
    return {
        "total": summary.total,
        "applied": summary.applied,
        "pending": summary.pending,
        "by_action": summary.by_action,
        "by_destination": summary.by_destination,
    }
