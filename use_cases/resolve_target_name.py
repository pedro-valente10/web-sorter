"""Escolhe um nome livre no destino, sem sobrescrever arquivos."""
from domain.file_name import NameAllocator, validate_file_name


class ResolveTargetName:
    def execute(self, name: str, taken_names: list[str]) -> str:
        return NameAllocator(taken_names).allocate(validate_file_name(name))
