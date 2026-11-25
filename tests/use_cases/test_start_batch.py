"""PlanBatch e StartBatch: mesma validação, só o segundo grava."""
import pytest

from domain.batch import BatchStatus, FileRef
from domain.errors import ValidationError
from use_cases.batch_request import BatchRequest
from use_cases.plan_batch import PlanBatch


def request(**changes):
    values = {
        "kind": "copy",
        "sources": ("Downloads",),
        "destination": "Organizado",
        "files": (FileRef(0, "a.pdf"), FileRef(0, "b.pdf")),
        "taken_names": ("a.pdf",),
    }
    values.update(changes)
    return BatchRequest(**values)


def test_plan_shows_final_names():
    view = PlanBatch().execute(1, request())
    assert view.progress.total == 2
    assert [i.target_name for i in view.items] == ["a (1).pdf", "b.pdf"]
    assert view.batch.id is None


def test_start_persists_batch_and_items(start_batch, batches, batch_items):
    view = start_batch.execute(1, request())
    assert batches.get(view.batch.id).status is BatchStatus.OPEN
    assert batches.get(view.batch.id).created_at is not None
    assert len(batch_items.list_by_batch(view.batch.id)) == 2


@pytest.mark.parametrize("changes", [
    {"same_folder": True},
    {"destination": None},
    {"files": ()},
    {"sources": ()},
    {"kind": "rename"},
])
def test_invalid_requests_are_neither_planned_nor_started(
    start_batch, batches, changes
):
    with pytest.raises(ValidationError):
        PlanBatch().execute(1, request(**changes))
    with pytest.raises(ValidationError):
        start_batch.execute(1, request(**changes))
    assert batches.list_by_user(1) == []


def test_delete_needs_no_destination(start_batch):
    view = start_batch.execute(
        1, request(kind="delete", destination=None, taken_names=())
    )
    assert view.batch.destination is None
