"""Servicio de autenticación: registro, login y revocación de refresh tokens.

Los refresh tokens revocados (logout) se guardan en Redis por su `jti` con TTL
igual al tiempo que le queda al token, de modo que expiran solos.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.redis_client import get_redis
from app.models.subscription import UserSubscription
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services import user_service
from app.utils.exceptions import ConflictError

_REVOKED_PREFIX = "revoked:refresh:"


def register_user(db: Session, data: RegisterRequest) -> User:
    """Crea un usuario nuevo con su subscription free por defecto."""
    if user_service.get_by_email(db, data.email):
        raise ConflictError("El email ya está registrado")
    if user_service.get_by_username(db, data.username):
        raise ConflictError("El nombre de usuario ya está en uso")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    user.subscription = UserSubscription()  # valores por defecto (plan free)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Devuelve el usuario si las credenciales son válidas y está activo."""
    user = user_service.get_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# -----------------------------------------------------------------------------
# Revocación de refresh tokens (logout)
# -----------------------------------------------------------------------------
def revoke_refresh_token(jti: str, expires_at: int) -> None:
    """Marca un refresh token como revocado hasta su expiración."""
    ttl = expires_at - int(datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        get_redis().setex(f"{_REVOKED_PREFIX}{jti}", ttl, "1")


def is_refresh_revoked(jti: str) -> bool:
    return bool(get_redis().exists(f"{_REVOKED_PREFIX}{jti}"))
