"""História 9: descartar um lote interrompido, sem tocar nos arquivos."""
from use_cases.batch_access import get_owned_batch
from use_cases.batch_view import BatchView
from use_cases.ports import (
    BatchItemRepository,
    BatchRepository,
    Clock,
    utc_now,
)


class DiscardBatch:
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
        batch.interrupt(self._clock())
        self._batches.update(batch)
        return BatchView(batch, self._items.progress(batch.id))
