"""História 9: retomar um lote fechado antes do fim."""
from domain.batch import ItemStatus
from use_cases.batch_access import get_owned_batch
from use_cases.batch_view import BatchView
from use_cases.ports import BatchItemRepository, BatchRepository


class ResumeBatch:
    def __init__(
        self, batches: BatchRepository, items: BatchItemRepository
    ):
        self._batches = batches
        self._items = items

    def execute(
        self, user_id: int, batch_id: int, taken_names: list[str]
    ) -> BatchView:
        """Devolve só o que falta, com nomes livres no destino atual."""
        batch = get_owned_batch(self._batches, batch_id, user_id)
        batch.require_open()
        pending = [
            item
            for item in self._items.list_by_batch(batch.id)
            if item.status is ItemStatus.PENDING
        ]
        pending = batch.assign_targets(pending, taken_names)
        self._items.save_all(pending)
        return BatchView(batch, self._items.progress(batch.id), pending)
