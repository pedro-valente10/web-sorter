"""Entidades Batch (lote) e BatchItem (arquivo do lote)."""
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from domain import failure_reason
from domain.errors import ValidationError
from domain.file_name import NameAllocator, validate_file_name

MAX_ITEMS = 20_000
MAX_SOURCES = 50
MAX_FOLDER_PATH_LENGTH = 1024


class BatchKind(str, Enum):
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"

    @classmethod
    def parse(cls, raw: str) -> "BatchKind":
        try:
            return cls(raw)
        except ValueError:
            valid = ", ".join(kind.value for kind in cls)
            raise ValidationError(
                f"Operação inválida. Use: {valid}."
            ) from None

    @property
    def needs_destination(self) -> bool:
        return self is not BatchKind.DELETE


class BatchStatus(str, Enum):
    OPEN = "open"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"


class ItemStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


def normalize_folder_path(raw: str | None) -> str:
    """Caminho de exibição, como 'Fotos/2025/Viagem'."""
    path = (raw or "").strip().strip("/")
    parts = path.split("/")
    invalid = (
        not path
        or len(path) > MAX_FOLDER_PATH_LENGTH
        or any(part in {"", ".", ".."} for part in parts)
    )
    if invalid:
        raise ValidationError("Nome de pasta inválido.")
    return path


@dataclass(frozen=True)
class FileRef:
    """Arquivo escolhido: em qual pasta de origem está e como se chama."""

    source: int
    name: str


@dataclass(frozen=True)
class BatchItem:
    position: int
    source: int
    name: str
    target_name: str | None = None
    status: ItemStatus = ItemStatus.PENDING
    error: str | None = None
    batch_id: int | None = None

    def __post_init__(self) -> None:
        validate_file_name(self.name)

    def _require_pending(self) -> None:
        if self.status is not ItemStatus.PENDING:
            raise ValidationError("Este arquivo já tem um resultado.")

    def succeed(self) -> "BatchItem":
        self._require_pending()
        return replace(self, status=ItemStatus.DONE, error=None)

    def fail(self, reason: str) -> "BatchItem":
        self._require_pending()
        return replace(self, status=ItemStatus.FAILED, error=reason)


@dataclass(frozen=True)
class BatchProgress:
    total: int = 0
    done: int = 0
    failed: int = 0

    @property
    def pending(self) -> int:
        return self.total - self.done - self.failed


@dataclass
class Batch:
    user_id: int
    kind: BatchKind
    sources: tuple[str, ...]
    destination: str | None = None
    id: int | None = None
    status: BatchStatus = BatchStatus.OPEN
    created_at: datetime | None = None
    finished_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 1 <= len(self.sources) <= MAX_SOURCES:
            raise ValidationError(
                f"Escolha de 1 a {MAX_SOURCES} pastas de origem."
            )
        self.sources = tuple(
            normalize_folder_path(path) for path in self.sources
        )
        if not self.kind.needs_destination:
            if self.destination is not None:
                raise ValidationError("Excluir não usa pasta de destino.")
            return
        if self.destination is None:
            raise ValidationError("Escolha a pasta de destino.")
        self.destination = normalize_folder_path(self.destination)

    @property
    def is_open(self) -> bool:
        return self.status is BatchStatus.OPEN

    def require_open(self) -> None:
        if not self.is_open:
            raise ValidationError("Este lote já foi encerrado.")

    def plan(
        self, files: Iterable[FileRef], taken_names: Iterable[str]
    ) -> list[BatchItem]:
        """Monta os itens do lote, já com um nome livre no destino."""
        files = list(files)
        if not files:
            raise ValidationError("Selecione ao menos um arquivo.")
        if len(files) > MAX_ITEMS:
            raise ValidationError(f"Limite de {MAX_ITEMS} arquivos por lote.")
        if len(set(files)) != len(files):
            raise ValidationError("Há arquivos repetidos na seleção.")
        if any(not 0 <= f.source < len(self.sources) for f in files):
            raise ValidationError("Pasta de origem inválida.")
        items = [
            BatchItem(position=position, source=file.source, name=file.name)
            for position, file in enumerate(files)
        ]
        return self.assign_targets(items, taken_names)

    def assign_targets(
        self, items: Iterable[BatchItem], taken_names: Iterable[str]
    ) -> list[BatchItem]:
        if not self.kind.needs_destination:
            return list(items)
        names = NameAllocator(taken_names)
        return [
            replace(item, target_name=names.allocate(item.name))
            for item in items
        ]

    def settle(
        self, item: BatchItem, step: str | None, code: str | None
    ) -> BatchItem:
        """Resultado de um arquivo; sem código de erro, deu certo."""
        self.require_open()
        if code is None:
            return item.succeed()
        if step not in failure_reason.STEPS:
            raise ValidationError("Etapa da falha inválida.")
        removing = step == failure_reason.REMOVE
        if removing and code == failure_reason.NOT_FOUND:
            return item.succeed()  # o original já tinha sumido
        if removing and self.kind is BatchKind.MOVE:
            return item.fail(failure_reason.describe_failed_removal(code))
        return item.fail(failure_reason.describe_failure(step, code))

    def finish(self, progress: BatchProgress, when: datetime) -> None:
        self.require_open()
        if progress.pending > 0:
            raise ValidationError("Ainda há arquivos sem resultado.")
        self.status = BatchStatus.FINISHED
        self.finished_at = when

    def interrupt(self, when: datetime) -> None:
        self.require_open()
        self.status = BatchStatus.INTERRUPTED
        self.finished_at = when
