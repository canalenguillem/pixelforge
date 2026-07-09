"""Utilidades de seguridad: hashing de contraseñas y JWT.

- Hashing con bcrypt (passlib).
- Tokens JWT access/refresh con python-jose.

La encriptación de API keys (Fernet) se implementará con la feature de Settings.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# bcrypt solo usa los primeros 72 bytes de la contraseña (y las versiones
# recientes lanzan error si se pasan más). Truncamos de forma explícita.
_BCRYPT_MAX_BYTES = 72


# -----------------------------------------------------------------------------
# Contraseñas
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en claro."""
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Comprueba una contraseña en claro contra su hash almacenado."""
    pw = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
    except ValueError:
        return False


# -----------------------------------------------------------------------------
# JWT
# -----------------------------------------------------------------------------
def _create_token(subject: str | int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str | int) -> str:
    """Access token de corta duración (JWT_EXPIRATION_HOURS)."""
    return _create_token(
        subject, ACCESS_TOKEN_TYPE, timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    )


def create_refresh_token(subject: str | int) -> str:
    """Refresh token de larga duración (JWT_REFRESH_EXPIRATION_DAYS)."""
    return _create_token(
        subject, REFRESH_TOKEN_TYPE, timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica y valida la firma/expiración de un JWT.

    Lanza jose.JWTError (o subclases como ExpiredSignatureError) si es inválido.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
