"""História 8: registrar o resultado de cada arquivo do lote."""
from domain.batch import BatchItem
from domain.errors import NotFoundError
from use_cases.batch_access import get_owned_batch
from use_cases.ports import BatchItemRepository, BatchRepository


class RecordItemResult:
    def __init__(
        self, batches: BatchRepository, items: BatchItemRepository
    ):
        self._batches = batches
        self._items = items

    def execute(
        self,
        user_id: int,
        batch_id: int,
        position: int,
        step: str | None = None,
        code: str | None = None,
    ) -> BatchItem:
        batch = get_owned_batch(self._batches, batch_id, user_id)
        item = self._items.get(batch.id, position)
        if item is None:
            raise NotFoundError("Arquivo não encontrado no lote.")
        settled = batch.settle(item, step, code)
        self._items.save_all([settled])
        return settled
