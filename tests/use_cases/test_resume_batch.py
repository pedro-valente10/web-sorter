"""ResumeBatch e DiscardBatch: lote fechado antes do fim."""
import pytest

from domain.batch import BatchStatus, ItemStatus
from domain.errors import NotFoundError, ValidationError
from use_cases.discard_batch import DiscardBatch
from use_cases.finish_batch import FinishBatch
from use_cases.record_item_result import RecordItemResult
from use_cases.resume_batch import ResumeBatch


@pytest.fixture
def record(batches, batch_items):
    return RecordItemResult(batches, batch_items)


@pytest.fixture
def resume(batches, batch_items):
    return ResumeBatch(batches, batch_items)


@pytest.fixture
def discard(batches, batch_items, clock):
    return DiscardBatch(batches, batch_items, clock)


def test_resumes_only_files_without_result(resume, record, move_batch):
    batch_id = move_batch.batch.id
    record.execute(1, batch_id, 0)
    record.execute(1, batch_id, 1, "read", "NotReadableError")

    view = resume.execute(1, batch_id, ["a.jpg"])

    assert [item.name for item in view.items] == ["c.jpg"]
    assert view.progress.pending == 1


def test_never_overwrites_what_appeared_in_the_destination(
    resume, move_batch, batch_items
):
    view = resume.execute(1, move_batch.batch.id, ["A.jpg", "b.jpg"])
    expected = ["a (1).jpg", "b (1).jpg", "c.jpg"]
    assert [item.target_name for item in view.items] == expected
    stored = batch_items.list_by_batch(move_batch.batch.id)
    assert [item.target_name for item in stored] == expected


def test_resumed_batch_can_be_finished(
    resume, record, move_batch, batches, batch_items, clock
):
    batch_id = move_batch.batch.id
    record.execute(1, batch_id, 0)
    for item in resume.execute(1, batch_id, []).items:
        record.execute(1, batch_id, item.position)
    view = FinishBatch(batches, batch_items, clock).execute(1, batch_id)
    assert view.progress.done == 3


def test_nothing_left_to_process_is_allowed(resume, record, move_batch):
    for position in range(3):
        record.execute(1, move_batch.batch.id, position)
    assert resume.execute(1, move_batch.batch.id, []).items == []


def test_discard_keeps_recorded_results(
    discard, record, move_batch, batches, batch_items
):
    batch_id = move_batch.batch.id
    record.execute(1, batch_id, 0)
    view = discard.execute(1, batch_id)
    assert (view.progress.done, view.progress.pending) == (1, 2)
    assert batches.get(batch_id).status is BatchStatus.INTERRUPTED
    assert batch_items.get(batch_id, 1).status is ItemStatus.PENDING


def test_discarded_batch_cannot_be_resumed(discard, resume, move_batch):
    discard.execute(1, move_batch.batch.id)
    with pytest.raises(ValidationError):
        resume.execute(1, move_batch.batch.id, [])


def test_another_user_cannot_resume_or_discard(
    discard, resume, move_batch
):
    with pytest.raises(NotFoundError):
        resume.execute(2, move_batch.batch.id, [])
    with pytest.raises(NotFoundError):
        discard.execute(2, move_batch.batch.id)
