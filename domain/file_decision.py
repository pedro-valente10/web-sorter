"""Entidade FileDecision: o que o usuário decidiu fazer com um arquivo."""
from dataclasses import dataclass, replace
from enum import Enum

from domain.errors import ValidationError

MAX_PATH_LENGTH = 1024


class Action(str, Enum):
    MOVE = "move"
    DELETE = "delete"
    KEEP = "keep"

    @classmethod
    def parse(cls, raw: str) -> "Action":
        try:
            return cls(raw)
        except ValueError:
            valid = ", ".join(action.value for action in cls)
            raise ValidationError(f"Ação inválida. Use: {valid}.") from None


def normalize_path(raw: str | None) -> str:
    """Caminho relativo à pasta escolhida, sempre com '/' e sem '..'."""
    path = (raw or "").replace("\\", "/").strip().strip("/")
    if not path or len(path) > MAX_PATH_LENGTH or ".." in path.split("/"):
        raise ValidationError("Caminho de arquivo inválido.")
    return path


@dataclass(frozen=True)
class FileDecision:
    session_id: int
    path: str
    action: Action
    destination: str | None = None
    applied: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", normalize_path(self.path))
        if self.action is Action.MOVE and not self.destination:
            raise ValidationError("Informe o destino para mover o arquivo.")
        if self.action is not Action.MOVE and self.destination:
            raise ValidationError("Só é possível ter destino ao mover.")

    def mark_applied(self) -> "FileDecision":
        return replace(self, applied=True)
