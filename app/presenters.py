"""Converte entidades e resultados de casos de uso em dicionários JSON."""
from datetime import datetime

from domain.batch import BatchItem
from domain.file_decision import FileDecision
from domain.sorting_session import SortingSession
from use_cases.batch_view import BatchView
from use_cases.get_session_summary import SessionSummary
from use_cases.summarize_extensions import ExtensionGroup


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


def extension_group_to_dict(group: ExtensionGroup) -> dict:
    return {
        "extension": group.extension,
        "description": group.description,
        "count": group.count,
        "indexes": group.indexes,
    }


def item_to_dict(item: BatchItem) -> dict:
    return {
        "position": item.position,
        "source": item.source,
        "name": item.name,
        "target_name": item.target_name,
        "status": item.status.value,
        "error": item.error,
    }


def batch_view_to_dict(view: BatchView, with_items: bool = True) -> dict:
    batch = view.batch
    result = {
        "id": batch.id,
        "kind": batch.kind.value,
        "sources": list(batch.sources),
        "destination": batch.destination,
        "status": batch.status.value,
        "created_at": _iso(batch.created_at),
        "finished_at": _iso(batch.finished_at),
        "progress": {
            "total": view.progress.total,
            "done": view.progress.done,
            "failed": view.progress.failed,
            "pending": view.progress.pending,
        },
    }
    if with_items:
        result["items"] = [item_to_dict(item) for item in view.items]
    return result


def _iso(when: datetime | None) -> str | None:
    return None if when is None else when.isoformat()
