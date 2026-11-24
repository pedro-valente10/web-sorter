"""Exceções de domínio, independentes de qualquer framework."""


class DomainError(Exception):
    """Base de todas as violações de regra de negócio."""


class ValidationError(DomainError):
    """Entrada ou estado que viola uma regra de negócio."""


class NotFoundError(DomainError):
    """Entidade inexistente (ou que não pertence ao usuário)."""


class UsernameAlreadyExistsError(DomainError):
    """Já existe um usuário com esse nome."""


class InvalidCredentialsError(DomainError):
    """Usuário ou senha não conferem."""
