"""Endpoints de uploads (subir, listar, detalle, eliminar, descargar).

Todas las rutas requieren autenticación y operan solo sobre los uploads
propios del usuario.
"""

import os
from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.schemas.upload import UploadListResponse, UploadRead
from app.services import upload_service
from app.utils.exceptions import AppError

router = APIRouter()

# Los PDFs (álbumes escaneados) pueden pesar bastante más que una foto suelta.
_MAX_PDF_BYTES = 200 * 1024 * 1024


@router.post("", response_model=UploadRead, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File(description="Foto a subir")],
) -> UploadRead:
    """Sube una foto (multipart/form-data), la valida y la registra."""
    content = await file.read()
    upload = upload_service.create_upload(
        db, current_user.id, file.filename, file.content_type, content
    )
    return UploadRead.model_validate(upload)


@router.post("/pdf", response_model=UploadListResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File(description="PDF con fotos a extraer")],
) -> UploadListResponse:
    """Extrae las fotos embebidas de un PDF y crea un upload por cada una."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise AppError("El fichero debe ser un PDF", 415)
    content = await file.read()
    if len(content) > _MAX_PDF_BYTES:
        raise AppError(f"El PDF supera el máximo de {_MAX_PDF_BYTES // (1024 * 1024)} MB", 413)

    stem = os.path.splitext(os.path.basename(file.filename or "pdf"))[0] or "pdf"
    uploads = upload_service.create_uploads_from_pdf(db, current_user.id, content, stem)
    return UploadListResponse(
        items=[UploadRead.model_validate(u) for u in uploads],
        total=len(uploads),
        page=1,
        page_size=len(uploads),
    )


@router.get("", response_model=UploadListResponse)
def list_uploads(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UploadListResponse:
    """Lista paginada de los uploads del usuario."""
    items, total = upload_service.list_uploads(db, current_user.id, page, page_size)
    return UploadListResponse(
        items=[UploadRead.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{upload_id}", response_model=UploadRead)
def get_upload(upload_id: int, current_user: CurrentUser, db: DbSession) -> UploadRead:
    """Detalles de un upload propio."""
    return UploadRead.model_validate(upload_service.get_upload(db, current_user.id, upload_id))


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(upload_id: int, current_user: CurrentUser, db: DbSession) -> None:
    """Elimina un upload propio (fichero + registro)."""
    upload_service.delete_upload(db, current_user.id, upload_id)


@router.get("/{upload_id}/download")
def download_upload(
    upload_id: int, current_user: CurrentUser, db: DbSession
) -> FileResponse:
    """Descarga el fichero original de un upload propio."""
    upload = upload_service.get_upload(db, current_user.id, upload_id)
    return FileResponse(
        upload.storage_path,
        filename=upload.original_filename,
        media_type=upload.mime_type or "application/octet-stream",
    )
