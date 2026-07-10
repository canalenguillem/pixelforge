"""Schemas Pydantic de jobs de procesamiento."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import WorkflowMode


class JobCreate(BaseModel):
    """Petición de creación de un job de restauración.

    Según `workflow_mode` se usan unos parámetros u otros:
    - epic: restoration_strength, codeformer_fidelity
    - flux: flux_denoise, enable_hdr_lora
    """

    upload_id: int
    # Encadenado: si se indica, la entrada es el resultado de ese job (no el original).
    parent_job_id: int | None = None
    workflow_mode: WorkflowMode = WorkflowMode.EPIC

    # --- Epic (SD1.5 + Tile ControlNet + CodeFormer) ---
    restoration_strength: float = Field(
        default=0.35,
        ge=0.0,
        le=0.8,
        description="Epic: denoise del pase de difusión. 0.2-0.35 fiel, 0.45+ limpia más pero altera",
    )
    codeformer_fidelity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Epic: restauración de caras. 0.0 = más calidad, 1.0 = más fiel",
    )

    # --- Flux Kontext (GGUF) ---
    enable_hdr_lora: bool = Field(
        default=True, description="Flux: aplicar HDR LoRA si está instalada (más realismo/rango)"
    )
    colorize: bool = Field(
        default=False, description="Flux: colorizar la foto (si no, restaura en blanco y negro)"
    )
    flux_denoise: float = Field(
        default=0.9,
        ge=0.5,
        le=1.0,
        description="Flux: fuerza de restauración. 0.5 sutil, 1.0 restauración completa (recomendado ~0.9)",
    )


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_id: int
    parent_job_id: int | None
    status: str
    job_type: str | None
    workflow_mode: str
    params: dict | None
    error_message: str | None
    processing_time_seconds: int | None
    created_at: datetime
    completed_at: datetime | None


class JobListResponse(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int
