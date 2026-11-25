"""Leitura e validação de tipos do corpo JSON das requisições."""
from flask import request

from domain.errors import ValidationError


def json_body() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Corpo JSON inválido.")
    return payload


def text(payload: dict, key: str, required: bool = True) -> str | None:
    value = payload.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"Campo '{key}' inválido.")
    return value


def text_list(payload: dict, key: str) -> list[str]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValidationError(f"Campo '{key}' inválido.")
    return value


def flag(payload: dict, key: str) -> bool:
    value = payload.get(key, False)
    if not isinstance(value, bool):
        raise ValidationError(f"Campo '{key}' inválido.")
    return value
