"""Servicio CRUD de usuarios (acceso a la tabla users)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def touch_last_login(db: Session, user: User) -> None:
    """Actualiza last_login al momento actual."""
    user.last_login = datetime.now(timezone.utc)
    db.commit()
