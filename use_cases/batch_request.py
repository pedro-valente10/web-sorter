"""Pedido de lote: entrada comum de PlanBatch e StartBatch."""
from dataclasses import dataclass

from domain.batch import Batch, BatchItem, BatchKind, FileRef
from domain.errors import ValidationError


@dataclass(frozen=True)
class BatchRequest:
    kind: str
    sources: tuple[str, ...]
    files: tuple[FileRef, ...]
    destination: str | None = None
    taken_names: tuple[str, ...] = ()
    same_folder: bool = False

    def build(self, user_id: int) -> tuple[Batch, list[BatchItem]]:
        if self.same_folder:
            raise ValidationError(
                "O destino é a própria pasta de origem. Escolha outra pasta."
            )
        batch = Batch(
            user_id=user_id,
            kind=BatchKind.parse(self.kind),
            sources=self.sources,
            destination=self.destination,
        )
        return batch, batch.plan(self.files, self.taken_names)
