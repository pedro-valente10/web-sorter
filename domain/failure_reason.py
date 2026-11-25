"""Traduz falhas técnicas do navegador para linguagem simples."""

READ = "read"
WRITE = "write"
REMOVE = "remove"
STEPS = frozenset({READ, WRITE, REMOVE})

NOT_FOUND = "NotFoundError"
_DEFAULT = "Não foi possível processar o arquivo."
_IN_USE = "O arquivo está em uso por outro programa."
_NO_WRITE_PERMISSION = "Sem permissão para gravar na pasta de destino."

_BY_STEP_AND_CODE = {
    (READ, "NotAllowedError"): "Sem permissão para ler o arquivo.",
    (WRITE, "NotAllowedError"): _NO_WRITE_PERMISSION,
    (WRITE, "NoModificationAllowedError"): _NO_WRITE_PERMISSION,
    (REMOVE, "NotAllowedError"):
        "Sem permissão para remover o arquivo da origem.",
    (READ, NOT_FOUND): "O arquivo não está mais na pasta de origem.",
    (WRITE, NOT_FOUND): "A pasta de destino não foi encontrada.",
    (REMOVE, NOT_FOUND): "O arquivo não está mais na pasta de origem.",
    (REMOVE, "InvalidStateError"): _IN_USE,
    (WRITE, "TargetExists"):
        "Já existe um arquivo com esse nome no destino.",
    (WRITE, "SizeMismatch"): "A cópia ficou incompleta e foi descartada.",
}

_BY_CODE = {
    "NoModificationAllowedError": _IN_USE,
    "InvalidModificationError": _IN_USE,
    "NotReadableError": "O arquivo está em uso ou mudou durante a leitura.",
    "QuotaExceededError": "Não há espaço suficiente no disco.",
    "TypeMismatchError": "Existe uma pasta com o mesmo nome do arquivo.",
    "SecurityError": "O navegador bloqueou o acesso a este arquivo.",
    "AbortError": "O navegador bloqueou a gravação deste arquivo.",
}


def describe_failure(step: str, code: str) -> str:
    specific = _BY_STEP_AND_CODE.get((step, code))
    return specific or _BY_CODE.get(code, _DEFAULT)


def describe_failed_removal(code: str) -> str:
    """A cópia deu certo, mas o original ficou na origem."""
    reason = describe_failure(REMOVE, code)
    return f"O arquivo foi copiado, mas continua na origem. {reason}"
