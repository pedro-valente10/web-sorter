"""Entidade SortingSession: o trabalho de um usuário em uma pasta."""
from dataclasses import dataclass, field
from datetime import datetime

from domain.errors import ValidationError

MAX_FOLDER_NAME_LENGTH = 255
MAX_DESTINATION_LENGTH = 60
MAX_DESTINATIONS = 50
_FORBIDDEN_CHARS = frozenset('\\/:*?"<>|')


def normalize_folder_name(raw: str | None) -> str:
    name = (raw or "").strip()
    if not name or len(name) > MAX_FOLDER_NAME_LENGTH:
        raise ValidationError("Nome de pasta inválido.")
    return name


def normalize_destination_name(raw: str | None) -> str:
    """Destinos viram subpastas, então precisam ser nomes de pasta válidos."""
    name = (raw or "").strip()
    invalid = (
        not name
        or len(name) > MAX_DESTINATION_LENGTH
        or name in {".", ".."}
        or name.endswith(".")
        or bool(_FORBIDDEN_CHARS & set(name))
    )
    if invalid:
        raise ValidationError(
            "Nome de destino inválido: use até 60 caracteres, sem "
            "\\ / : * ? \" < > | e sem terminar em ponto."
        )
    return name


@dataclass
class SortingSession:
    user_id: int
    folder_name: str
    id: int | None = None
    destinations: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def find_destination(self, name: str | None) -> str | None:
        """Devolve o destino cadastrado (ignorando maiúsculas) ou None."""
        wanted = (name or "").strip().casefold()
        for destination in self.destinations:
            if destination.casefold() == wanted:
                return destination
        return None

    def add_destination(self, raw_name: str | None) -> str:
        name = normalize_destination_name(raw_name)
        if self.find_destination(name) is not None:
            raise ValidationError("Esse destino já existe.")
        if len(self.destinations) >= MAX_DESTINATIONS:
            raise ValidationError("Limite de destinos atingido.")
        self.destinations.append(name)
        return name

    def touch(self, when: datetime) -> None:
        self.updated_at = when
