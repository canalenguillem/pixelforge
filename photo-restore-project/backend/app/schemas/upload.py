"""Schemas Pydantic de upload."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadRead(BaseModel):
    """Vista pública de un upload (no expone el storage_path interno)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_size: int | None
    mime_type: str | None
    width: int | None
    height: int | None
    status: str
    created_at: datetime


class UploadListResponse(BaseModel):
    """Listado paginado de uploads."""

    items: list[UploadRead]
    total: int
    page: int
    page_size: int
