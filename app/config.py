"""Configuração da aplicação (lida do ambiente, com padrões para dev)."""
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

DEFAULT_INSTANCE_DIR = Path(__file__).resolve().parent.parent / "instance"


@dataclass(frozen=True)
class Config:
    database_path: str
    secret_key: str

    @classmethod
    def from_env(cls) -> "Config":
        instance_dir = Path(
            os.environ.get("INSTANCE_DIR", DEFAULT_INSTANCE_DIR)
        )
        instance_dir.mkdir(parents=True, exist_ok=True)
        database_path = os.environ.get(
            "DATABASE_PATH", str(instance_dir / "web_sorter.db")
        )
        secret_key = os.environ.get("SECRET_KEY") or _load_or_create_secret(
            instance_dir / "secret_key"
        )
        return cls(database_path=database_path, secret_key=secret_key)


def _load_or_create_secret(path: Path) -> str:
    """Mantém a chave entre reinícios para não derrubar os logins."""
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    secret = secrets.token_hex(32)
    path.write_text(secret, encoding="utf-8")
    return secret
