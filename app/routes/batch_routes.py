"""API JSON dos lotes: resumo, planejamento, execução e histórico."""
from flask import Blueprint, jsonify

from app.container import get_container
from app.json_input import flag, json_body, text, text_list
from app.presenters import (
    batch_view_to_dict,
    extension_group_to_dict,
    item_to_dict,
)
from app.security import current_user_id, login_required
from domain.batch import FileRef
from domain.errors import ValidationError
from use_cases.batch_request import BatchRequest

bp = Blueprint("batch", __name__, url_prefix="/api")


def _file_refs(payload: dict) -> tuple[FileRef, ...]:
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValidationError("Campo 'files' inválido.")
    refs = []
    for entry in files:
        source = entry.get("source") if isinstance(entry, dict) else None
        if type(source) is not int:
            raise ValidationError("Campo 'files' inválido.")
        refs.append(FileRef(source=source, name=text(entry, "name")))
    return tuple(refs)


def _batch_request() -> BatchRequest:
    payload = json_body()
    return BatchRequest(
        kind=text(payload, "kind"),
        sources=tuple(text_list(payload, "sources")),
        files=_file_refs(payload),
        destination=text(payload, "destination", required=False),
        taken_names=tuple(text_list(payload, "taken_names")),
        same_folder=flag(payload, "same_folder"),
    )


@bp.post("/extensions")
@login_required
def summarize_extensions():
    groups = get_container().summarize_extensions.execute(
        text_list(json_body(), "files")
    )
    return jsonify(extensions=[extension_group_to_dict(g) for g in groups])


@bp.post("/target-name")
@login_required
def resolve_target_name():
    payload = json_body()
    name = get_container().resolve_target_name.execute(
        text(payload, "name"), text_list(payload, "taken_names")
    )
    return jsonify(name=name)


@bp.post("/batches/plan")
@login_required
def plan_batch():
    view = get_container().plan_batch.execute(
        current_user_id(), _batch_request()
    )
    return jsonify(batch_view_to_dict(view))


@bp.post("/batches")
@login_required
def start_batch():
    view = get_container().start_batch.execute(
        current_user_id(), _batch_request()
    )
    return jsonify(batch_view_to_dict(view)), 201


@bp.get("/batches")
@login_required
def list_batches():
    views = get_container().list_batches.execute(current_user_id())
    return jsonify(
        batches=[batch_view_to_dict(v, with_items=False) for v in views]
    )


@bp.get("/batches/<int:batch_id>")
@login_required
def get_batch(batch_id: int):
    view = get_container().get_batch.execute(current_user_id(), batch_id)
    return jsonify(batch_view_to_dict(view))


@bp.post("/batches/<int:batch_id>/items/<int:position>/result")
@login_required
def record_item_result(batch_id: int, position: int):
    payload = json_body()
    item = get_container().record_item_result.execute(
        current_user_id(),
        batch_id,
        position,
        text(payload, "step", required=False),
        text(payload, "code", required=False),
    )
    return jsonify(item_to_dict(item))


@bp.post("/batches/<int:batch_id>/finish")
@login_required
def finish_batch(batch_id: int):
    view = get_container().finish_batch.execute(current_user_id(), batch_id)
    return jsonify(batch_view_to_dict(view))


@bp.post("/batches/<int:batch_id>/resume")
@login_required
def resume_batch(batch_id: int):
    view = get_container().resume_batch.execute(
        current_user_id(), batch_id, text_list(json_body(), "taken_names")
    )
    return jsonify(batch_view_to_dict(view))


@bp.post("/batches/<int:batch_id>/discard")
@login_required
def discard_batch(batch_id: int):
    view = get_container().discard_batch.execute(current_user_id(), batch_id)
    return jsonify(batch_view_to_dict(view, with_items=False))
