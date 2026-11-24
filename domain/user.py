"""Entidade User e regras de validação de credenciais."""
import re
from dataclasses import dataclass

from domain.errors import ValidationError

MIN_PASSWORD_LENGTH = 8
_USERNAME_PATTERN = re.compile(r"[a-z0-9_.-]{3,30}")


def normalize_username(raw: str | None) -> str:
    """Devolve o usuário em minúsculas ou levanta ValidationError."""
    username = (raw or "").strip().lower()
    if not _USERNAME_PATTERN.fullmatch(username):
        raise ValidationError(
            "O usuário deve ter de 3 a 30 caracteres "
            "(letras, números, '_', '.' ou '-')."
        )
    return username


def validate_password(raw: str | None) -> None:
    if len(raw or "") < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres."
        )


@dataclass(frozen=True)
class User:
    id: int | None
    username: str
    password_hash: str
