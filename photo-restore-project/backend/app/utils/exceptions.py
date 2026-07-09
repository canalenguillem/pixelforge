"""Excepciones de dominio de la aplicación.

Se traducen a respuestas HTTP mediante un exception handler en main.py.
"""


class AppError(Exception):
    """Error de aplicación con código HTTP asociado."""

    status_code: int = 400

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class ConflictError(AppError):
    """Recurso en conflicto (p. ej. email/username ya registrado)."""

    status_code = 409


class AuthError(AppError):
    """Fallo de autenticación / credenciales inválidas."""

    status_code = 401

    def __init__(self, message: str = "Credenciales inválidas") -> None:
        super().__init__(message)


class NotFoundError(AppError):
    """Recurso no encontrado."""

    status_code = 404
