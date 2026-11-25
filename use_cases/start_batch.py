"""História 7: confirmar e iniciar a cópia, movimentação ou exclusão."""
from domain.batch import BatchProgress
from use_cases.batch_request import BatchRequest
from use_cases.batch_view import BatchView
from use_cases.ports import BatchRepository, Clock, utc_now


class StartBatch:
    def __init__(self, batches: BatchRepository, clock: Clock = utc_now):
        self._batches = batches
        self._clock = clock

    def execute(self, user_id: int, request: BatchRequest) -> BatchView:
        batch, items = request.build(user_id)
        batch.created_at = self._clock()
        batch, items = self._batches.add(batch, items)
        return BatchView(batch, BatchProgress(total=len(items)), items)
