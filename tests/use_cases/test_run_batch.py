"""RecordItemResult e FinishBatch."""
import pytest

from domain.batch import BatchStatus, ItemStatus
from domain.errors import NotFoundError, ValidationError
from use_cases.finish_batch import FinishBatch
from use_cases.record_item_result import RecordItemResult


@pytest.fixture
def record(batches, batch_items):
    return RecordItemResult(batches, batch_items)


@pytest.fixture
def finish(batches, batch_items, clock):
    return FinishBatch(batches, batch_items, clock)


def test_records_success(record, move_batch, batch_items):
    record.execute(1, move_batch.batch.id, 0)
    stored = batch_items.get(move_batch.batch.id, 0)
    assert stored.status is ItemStatus.DONE


def test_one_failure_does_not_stop_the_others(
    record, finish, move_batch
):
    batch_id = move_batch.batch.id
    record.execute(1, batch_id, 0)
    record.execute(1, batch_id, 1, "write", "NotAllowedError")
    record.execute(1, batch_id, 2)

    view = finish.execute(1, batch_id)

    assert (view.progress.done, view.progress.failed) == (2, 1)
    failed = [i for i in view.items if i.status is ItemStatus.FAILED]
    assert [(i.name, i.error) for i in failed] == [
        ("b.jpg", "Sem permissão para gravar na pasta de destino."),
    ]


def test_unknown_file_is_not_found(record, move_batch):
    with pytest.raises(NotFoundError):
        record.execute(1, move_batch.batch.id, 99)


def test_result_cannot_be_changed(record, move_batch):
    record.execute(1, move_batch.batch.id, 0)
    with pytest.raises(ValidationError):
        record.execute(1, move_batch.batch.id, 0, "read", "NotFoundError")


def test_another_user_cannot_touch_the_batch(record, finish, move_batch):
    with pytest.raises(NotFoundError):
        record.execute(2, move_batch.batch.id, 0)
    with pytest.raises(NotFoundError):
        finish.execute(2, move_batch.batch.id)


def test_cannot_finish_with_pending_files(
    record, finish, move_batch, batches
):
    record.execute(1, move_batch.batch.id, 0)
    with pytest.raises(ValidationError):
        finish.execute(1, move_batch.batch.id)
    assert batches.get(move_batch.batch.id).status is BatchStatus.OPEN


def test_finish_stores_status_and_date(
    record, finish, move_batch, batches
):
    for position in range(3):
        record.execute(1, move_batch.batch.id, position)
    finish.execute(1, move_batch.batch.id)
    stored = batches.get(move_batch.batch.id)
    assert stored.status is BatchStatus.FINISHED
    assert stored.finished_at > stored.created_at
