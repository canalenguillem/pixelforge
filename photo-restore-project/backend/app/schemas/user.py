"""Schemas Pydantic de usuario."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    """Vista pública de un usuario (nunca incluye el password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    full_name: str | None
    avatar_url: str | None
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: datetime | None
