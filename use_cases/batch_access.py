"""Garante que o lote existe e pertence ao usuário."""
from domain.batch import Batch
from domain.errors import NotFoundError
from use_cases.ports import BatchRepository


def get_owned_batch(
    batches: BatchRepository, batch_id: int, user_id: int
) -> Batch:
    batch = batches.get(batch_id)
    if batch is None or batch.user_id != user_id:
        raise NotFoundError("Lote não encontrado.")
    return batch
