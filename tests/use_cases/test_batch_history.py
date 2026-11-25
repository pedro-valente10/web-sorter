"""ListBatches e GetBatch."""
import pytest

from domain.errors import NotFoundError
from use_cases.get_batch import GetBatch
from use_cases.list_batches import ListBatches
from use_cases.record_item_result import RecordItemResult


@pytest.fixture
def history(batches, batch_items):
    return ListBatches(batches, batch_items)


@pytest.fixture
def get_batch(batches, batch_items):
    return GetBatch(batches, batch_items)


def test_lists_only_the_users_batches_with_progress(
    history, move_batch, batches, batch_items
):
    RecordItemResult(batches, batch_items).execute(
        1, move_batch.batch.id, 0
    )
    [view] = history.execute(1)
    assert (view.progress.total, view.progress.done) == (3, 1)
    assert view.items == []
    assert history.execute(2) == []


def test_details_bring_every_file(get_batch, move_batch):
    view = get_batch.execute(1, move_batch.batch.id)
    assert [item.name for item in view.items] == ["a.jpg", "b.jpg", "c.jpg"]


def test_another_users_batch_is_not_found(get_batch, move_batch):
    with pytest.raises(NotFoundError):
        get_batch.execute(2, move_batch.batch.id)
