"""História 6: ver as extensões das pastas de origem e suas quantidades."""
from dataclasses import dataclass

from domain.batch import MAX_ITEMS
from domain.errors import ValidationError
from domain.file_name import (
    describe_extension,
    extension_of,
    validate_file_name,
)


@dataclass(frozen=True)
class ExtensionGroup:
    extension: str
    description: str
    indexes: list[int]

    @property
    def count(self) -> int:
        return len(self.indexes)


class SummarizeExtensions:
    def execute(self, file_names: list[str]) -> list[ExtensionGroup]:
        """Agrupa por extensão, da mais comum para a menos comum."""
        if len(file_names) > MAX_ITEMS:
            raise ValidationError(f"Limite de {MAX_ITEMS} arquivos.")
        indexes: dict[str, list[int]] = {}
        for index, name in enumerate(file_names):
            extension = extension_of(validate_file_name(name))
            indexes.setdefault(extension, []).append(index)
        groups = [
            ExtensionGroup(extension, describe_extension(extension), found)
            for extension, found in indexes.items()
        ]
        return sorted(groups, key=lambda g: (-g.count, g.extension))
