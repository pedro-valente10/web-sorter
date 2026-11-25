"""História 8: concluir o lote e obter o resumo com os erros."""
from use_cases.batch_access import get_owned_batch
from use_cases.batch_view import BatchView
from use_cases.ports import (
    BatchItemRepository,
    BatchRepository,
    Clock,
    utc_now,
)


class FinishBatch:
    def __init__(
        self,
        batches: BatchRepository,
        items: BatchItemRepository,
        clock: Clock = utc_now,
    ):
        self._batches = batches
        self._items = items
        self._clock = clock

    def execute(self, user_id: int, batch_id: int) -> BatchView:
        batch = get_owned_batch(self._batches, batch_id, user_id)
        progress = self._items.progress(batch.id)
        batch.finish(progress, self._clock())
        self._batches.update(batch)
        return BatchView(
            batch, progress, self._items.list_by_batch(batch.id)
        )
