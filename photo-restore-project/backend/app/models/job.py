"""Modelo ORM ProcessingJob (tabla: processing_jobs).

Mapea la tabla `processing_jobs` creada por backend/sql/init.sql.
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import JobStatus, JobType
from app.db.base import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False
    )
    # Job del que proviene la imagen de entrada (encadenado). NULL = sobre el original.
    parent_job_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("processing_jobs.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=JobStatus.QUEUED.value, nullable=False, index=True
    )
    job_type: Mapped[str | None] = mapped_column(String(100), default=JobType.RESTORATION.value)
    workflow_mode: Mapped[str] = mapped_column(String(20), default="epic", nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProcessingJob id={self.id} status={self.status!r}>"
