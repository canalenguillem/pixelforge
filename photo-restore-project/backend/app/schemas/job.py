"""Schemas Pydantic de jobs de procesamiento."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    """Petición de creación de un job de restauración."""

    upload_id: int
    restoration_strength: float = Field(
        default=0.35,
        ge=0.0,
        le=0.8,
        description="Fuerza del pase de difusión (denoise). 0.2-0.35 fiel, 0.45+ limpia más pero altera",
    )
    codeformer_fidelity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Restauración de caras: 0.0 = más calidad, 1.0 = más fiel al original",
    )


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_id: int
    status: str
    job_type: str | None
    error_message: str | None
    processing_time_seconds: int | None
    created_at: datetime
    completed_at: datetime | None


class JobListResponse(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int
