"""Modelo ORM UserSubscription (tabla: user_subscriptions).

Mapea la tabla `user_subscriptions` creada por backend/sql/init.sql.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    DEFAULT_CREDITS_BALANCE,
    DEFAULT_MONTHLY_UPLOADS_LIMIT,
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    PlanType,
)
from app.db.base import Base


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    plan_type: Mapped[str] = mapped_column(String(50), default=PlanType.FREE.value)
    credits_balance: Mapped[int] = mapped_column(Integer, default=DEFAULT_CREDITS_BALANCE)
    credits_used: Mapped[int] = mapped_column(Integer, default=0)
    monthly_uploads_limit: Mapped[int] = mapped_column(
        Integer, default=DEFAULT_MONTHLY_UPLOADS_LIMIT
    )
    uploads_used: Mapped[int] = mapped_column(Integer, default=0)
    api_rate_limit: Mapped[int] = mapped_column(Integer, default=DEFAULT_RATE_LIMIT_PER_MINUTE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    renewal_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="subscription")  # noqa: F821
