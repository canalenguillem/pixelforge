"""Endpoints de autenticación (register, login, refresh, logout, me)."""

from fastapi import APIRouter, status
from jose import JWTError

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service, user_service
from app.utils.exceptions import AppError, AuthError

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession) -> UserRead:
    """Registra un usuario nuevo (con subscription free por defecto).

    El registro público está desactivado (el alta será por invitación). Se
    reactiva con ALLOW_REGISTRATION=true.
    """
    if not settings.ALLOW_REGISTRATION:
        raise AppError("El registro está deshabilitado", 403)
    user = auth_service.register_user(db, data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    """Valida credenciales y devuelve access + refresh tokens."""
    user = auth_service.authenticate(db, data.email, data.password)
    if user is None:
        raise AuthError()
    user_service.touch_last_login(db, user)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: DbSession) -> TokenResponse:
    """Emite nuevos tokens a partir de un refresh token válido y no revocado."""
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise AuthError("Refresh token inválido o expirado")

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise AuthError("Token no es de tipo refresh")

    jti = payload.get("jti")
    if jti and auth_service.is_refresh_revoked(jti):
        raise AuthError("La sesión ha sido cerrada")

    subject = payload.get("sub")
    if subject is None:
        raise AuthError("Refresh token inválido")

    user = user_service.get_by_id(db, int(subject))
    if user is None or not user.is_active:
        raise AuthError()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest) -> None:
    """Revoca el refresh token (queda inutilizable hasta su expiración)."""
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        # Token ya inválido/expirado: logout es idempotente, no hay nada que revocar.
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        auth_service.revoke_refresh_token(jti, int(exp))


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    """Devuelve la información del usuario autenticado."""
    return UserRead.model_validate(current_user)
