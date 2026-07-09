"""Dependencias reutilizables de la API (DB session, usuario autenticado)."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.models.user import User
from app.services import user_service

DbSession = Annotated[Session, Depends(get_db)]

bearer_scheme = HTTPBearer(auto_error=True)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    """Resuelve el usuario a partir del access token del header Authorization."""
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise _credentials_exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise _credentials_exc

    subject = payload.get("sub")
    if subject is None:
        raise _credentials_exc

    user = user_service.get_by_id(db, int(subject))
    if user is None or not user.is_active:
        raise _credentials_exc

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
