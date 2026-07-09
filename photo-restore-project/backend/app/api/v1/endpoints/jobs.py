"""Endpoints de jobs de procesamiento (crear, listar, estado, resultado, borrar).

El procesamiento es SÍNCRONO por ahora (se moverá a Celery + WebSocket).
Todas las rutas requieren autenticación y operan solo sobre jobs propios.
"""

import os
from typing import Annotated

from fastapi import APIRouter, Query, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.schemas.job import JobCreate, JobListResponse, JobRead
from app.services import job_service
from app.utils.exceptions import AppError

router = APIRouter()


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(data: JobCreate, current_user: CurrentUser, db: DbSession) -> JobRead:
    """Crea y procesa un job de restauración sobre un upload propio."""
    job = job_service.create_and_run(
        db,
        current_user.id,
        data.upload_id,
        restoration_strength=data.restoration_strength,
        codeformer_fidelity=data.codeformer_fidelity,
    )
    return JobRead.model_validate(job)


@router.get("", response_model=JobListResponse)
def list_jobs(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JobListResponse:
    """Lista paginada de los jobs del usuario."""
    items, total = job_service.list_jobs(db, current_user.id, page, page_size)
    return JobListResponse(
        items=[JobRead.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, current_user: CurrentUser, db: DbSession) -> JobRead:
    """Estado/detalle de un job propio."""
    return JobRead.model_validate(job_service.get_job(db, current_user.id, job_id))


@router.get("/{job_id}/result")
def get_job_result(job_id: int, current_user: CurrentUser, db: DbSession) -> FileResponse:
    """Descarga la imagen restaurada de un job completado."""
    job = job_service.get_job(db, current_user.id, job_id)
    if job.status != "completed" or not job.processed_image_path:
        raise AppError("El job aún no tiene resultado disponible", 409)
    if not os.path.exists(job.processed_image_path):
        raise AppError("El fichero del resultado no existe", 404)
    return FileResponse(
        job.processed_image_path,
        filename=f"restored_{job.id}{os.path.splitext(job.processed_image_path)[1]}",
        media_type="image/png",
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, current_user: CurrentUser, db: DbSession) -> None:
    """Elimina un job propio (resultado + registro)."""
    job_service.delete_job(db, current_user.id, job_id)
