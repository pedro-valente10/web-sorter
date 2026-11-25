"""História 10: consultar o histórico de operações."""
from use_cases.batch_view import BatchView
from use_cases.ports import BatchItemRepository, BatchRepository


class ListBatches:
    def __init__(
        self, batches: BatchRepository, items: BatchItemRepository
    ):
        self._batches = batches
        self._items = items

    def execute(self, user_id: int) -> list[BatchView]:
        return [
            BatchView(batch, self._items.progress(batch.id))
            for batch in self._batches.list_by_user(user_id)
        ]
