"""História 10: ver os arquivos e erros de uma operação."""
from use_cases.batch_access import get_owned_batch
from use_cases.batch_view import BatchView
from use_cases.ports import BatchItemRepository, BatchRepository


class GetBatch:
    def __init__(
        self, batches: BatchRepository, items: BatchItemRepository
    ):
        self._batches = batches
        self._items = items

    def execute(self, user_id: int, batch_id: int) -> BatchView:
        batch = get_owned_batch(self._batches, batch_id, user_id)
        return BatchView(
            batch,
            self._items.progress(batch.id),
            self._items.list_by_batch(batch.id),
        )
