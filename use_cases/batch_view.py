"""Saída comum dos casos de uso de lote."""
from dataclasses import dataclass, field

from domain.batch import Batch, BatchItem, BatchProgress


@dataclass(frozen=True)
class BatchView:
    batch: Batch
    progress: BatchProgress
    items: list[BatchItem] = field(default_factory=list)
