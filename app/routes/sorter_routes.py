"""Tela principal e API JSON do organizador."""
from flask import Blueprint, jsonify, render_template, session

from app.container import get_container
from app.json_input import json_body, text
from app.presenters import (
    decision_to_dict,
    session_to_dict,
    summary_to_dict,
)
from app.security import current_user_id, login_required

bp = Blueprint("sorter", __name__)


@bp.get("/")
@login_required
def index():
    return render_template("workspace.html", username=session.get("username"))


@bp.get("/api/sessions")
@login_required
def list_sessions():
    sessions = get_container().list_sessions.execute(current_user_id())
    return jsonify(sessions=[session_to_dict(s) for s in sessions])


@bp.post("/api/sessions")
@login_required
def open_session():
    folder_name = text(json_body(), "folder_name")
    state = get_container().open_session.execute(
        current_user_id(), folder_name
    )
    return jsonify(
        session=session_to_dict(state.session),
        decisions=[decision_to_dict(d) for d in state.decisions],
    )


@bp.post("/api/sessions/<int:session_id>/destinations")
@login_required
def add_destination(session_id: int):
    name = text(json_body(), "name")
    updated = get_container().add_destination.execute(
        current_user_id(), session_id, name
    )
    return jsonify(session_to_dict(updated)), 201


@bp.put("/api/sessions/<int:session_id>/decisions")
@login_required
def record_decision(session_id: int):
    payload = json_body()
    decision = get_container().record_decision.execute(
        current_user_id(),
        session_id,
        text(payload, "path"),
        text(payload, "action"),
        text(payload, "destination", required=False),
    )
    return jsonify(decision_to_dict(decision))


@bp.delete("/api/sessions/<int:session_id>/decisions")
@login_required
def undo_decision(session_id: int):
    removed = get_container().undo_decision.execute(
        current_user_id(), session_id, text(json_body(), "path")
    )
    return jsonify(removed=removed)


@bp.post("/api/sessions/<int:session_id>/decisions/applied")
@login_required
def mark_applied(session_id: int):
    decision = get_container().mark_decision_applied.execute(
        current_user_id(), session_id, text(json_body(), "path")
    )
    return jsonify(decision_to_dict(decision))


@bp.get("/api/sessions/<int:session_id>/summary")
@login_required
def summary(session_id: int):
    result = get_container().get_session_summary.execute(
        current_user_id(), session_id
    )
    return jsonify(summary_to_dict(result))
