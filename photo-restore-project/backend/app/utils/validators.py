"""Validadores de uploads (extensión y tamaño)."""

import os

from app.core.config import settings
from app.utils.exceptions import AppError


def get_extension(filename: str | None) -> str:
    """Extensión en minúsculas sin punto (p. ej. 'jpg'). '' si no tiene."""
    return os.path.splitext(filename or "")[1].lower().lstrip(".")


def validate_upload(filename: str | None, size: int) -> str:
    """Valida extensión permitida y tamaño. Devuelve la extensión normalizada.

    Lanza AppError (con su código HTTP) si algo no cumple.
    """
    if size == 0:
        raise AppError("El archivo está vacío", 400)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise AppError(
            f"El archivo supera el máximo de {settings.MAX_FILE_SIZE_MB} MB",
            413,  # Payload Too Large
        )

    ext = get_extension(filename)
    allowed = settings.allowed_extensions_set
    if ext not in allowed:
        raise AppError(
            f"Extensión no permitida: '.{ext}'. Permitidas: {', '.join(sorted(allowed))}",
            415,  # Unsupported Media Type
        )

    return ext
