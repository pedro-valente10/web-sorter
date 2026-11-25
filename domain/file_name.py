"""Regras sobre nomes de arquivo: validação, extensão e nomes repetidos."""
from collections.abc import Iterable

from domain.errors import ValidationError

MAX_FILE_NAME_LENGTH = 255

_DESCRIPTIONS = {
    ".pdf": "Arquivos PDF",
    ".jpg": "Imagens JPEG",
    ".jpeg": "Imagens JPEG",
    ".png": "Imagens PNG",
    ".gif": "Imagens GIF",
    ".webp": "Imagens WebP",
    ".bmp": "Imagens BMP",
    ".svg": "Imagens SVG",
    ".heic": "Imagens HEIC",
    ".mp4": "Vídeos MP4",
    ".mov": "Vídeos MOV",
    ".mkv": "Vídeos MKV",
    ".webm": "Vídeos WebM",
    ".mp3": "Áudios MP3",
    ".wav": "Áudios WAV",
    ".doc": "Documentos Word",
    ".docx": "Documentos Word",
    ".xls": "Planilhas Excel",
    ".xlsx": "Planilhas Excel",
    ".ppt": "Apresentações PowerPoint",
    ".pptx": "Apresentações PowerPoint",
    ".csv": "Planilhas CSV",
    ".txt": "Arquivos de texto",
    ".md": "Arquivos Markdown",
    ".zip": "Arquivos compactados ZIP",
    ".rar": "Arquivos compactados RAR",
    ".7z": "Arquivos compactados 7z",
    ".exe": "Programas do Windows",
    ".py": "Arquivos Python",
    ".c": "Arquivos de código C",
    ".js": "Arquivos JavaScript",
    ".html": "Páginas HTML",
    ".css": "Folhas de estilo CSS",
    ".java": "Arquivos Java",
    ".json": "Arquivos JSON",
}


def validate_file_name(raw: str | None) -> str:
    """Aceita só um nome de arquivo, nunca um caminho."""
    name = raw or ""
    invalid = (
        not name.strip()
        or len(name) > MAX_FILE_NAME_LENGTH
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
    )
    if invalid:
        raise ValidationError("Nome de arquivo inválido.")
    return name


def split_name(name: str) -> tuple[str, str]:
    """Separa 'foto.JPG' em ('foto', '.JPG'); '.env' não tem extensão."""
    dot = name.rfind(".")
    if dot <= 0 or dot == len(name) - 1:
        return name, ""
    return name[:dot], name[dot:]


def extension_of(name: str) -> str:
    """Extensão em minúsculas, com o ponto, ou '' quando não há."""
    return split_name(name)[1].lower()


def describe_extension(extension: str) -> str:
    if not extension:
        return "Arquivos sem extensão"
    return _DESCRIPTIONS.get(
        extension, f"Arquivos {extension[1:].upper()}"
    )


class NameAllocator:
    """Distribui nomes livres em uma pasta: 'foto.jpg' -> 'foto (1).jpg'.

    Ignora maiúsculas, como o sistema de arquivos do Windows.
    """

    def __init__(self, taken: Iterable[str] = ()):
        self._taken = {name.casefold() for name in taken}
        self._next_suffix: dict[str, int] = {}

    def allocate(self, name: str) -> str:
        base, extension = split_name(name)
        key = name.casefold()
        suffix = self._next_suffix.get(key, 1)
        candidate = name
        while candidate.casefold() in self._taken:
            candidate = f"{base} ({suffix}){extension}"
            suffix += 1
        self._next_suffix[key] = suffix
        self._taken.add(candidate.casefold())
        return candidate
