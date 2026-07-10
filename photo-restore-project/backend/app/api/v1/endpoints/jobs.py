"""Endpoints de jobs de procesamiento (crear, listar, estado, resultado, stream).

El procesamiento es ASÍNCRONO (Celery). `POST /jobs` encola y responde 202;
el progreso en tiempo real llega por el WebSocket `/jobs/{id}/stream`.
"""

import json
import os
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, File, Form, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from jose import JWTError

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import SessionLocal
from app.models.job import ProcessingJob
from app.schemas.job import JobCreate, JobListResponse, JobRead
from app.services import job_service
from app.utils.exceptions import AppError

router = APIRouter()


@router.post("", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def create_job(data: JobCreate, current_user: CurrentUser, db: DbSession) -> JobRead:
    """Encola un job de restauración (async). Devuelve el job en estado 'queued'."""
    job = job_service.enqueue_restoration(
        db,
        current_user.id,
        data.upload_id,
        restoration_strength=data.restoration_strength,
        codeformer_fidelity=data.codeformer_fidelity,
    )
    return JobRead.model_validate(job)


@router.post("/inpaint", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_inpaint_job(
    current_user: CurrentUser,
    db: DbSession,
    upload_id: Annotated[int, Form()],
    mask: Annotated[UploadFile, File(description="Máscara PNG (blanco = reparar)")],
    grow: Annotated[int, Form()] = 8,
) -> JobRead:
    """Encola un job de eliminación de daño: inpainta la zona enmascarada."""
    mask_bytes = await mask.read()
    job = job_service.enqueue_inpaint(db, current_user.id, upload_id, mask_bytes, grow)
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
    """Estado/detalle de un job propio (para polling)."""
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


@router.websocket("/{job_id}/stream")
async def job_stream(
    websocket: WebSocket,
    job_id: int,
    token: Annotated[str, Query(description="Access token JWT")],
) -> None:
    """WebSocket de progreso en tiempo real de un job.

    Auth por query param `token` (el navegador no puede poner headers en un WS).
    Reenvía los eventos publicados por el worker en `job:{id}:progress`.
    """
    # 1) Autenticación
    try:
        payload = decode_token(token)
        if payload.get("type") != ACCESS_TOKEN_TYPE or payload.get("sub") is None:
            raise JWTError("token inválido")
        user_id = int(payload["sub"])
    except (JWTError, ValueError):
        await websocket.close(code=4401)
        return

    # 2) Propiedad del job
    db = SessionLocal()
    try:
        job = db.get(ProcessingJob, job_id)
        if job is None or job.user_id != user_id:
            await websocket.close(code=4404)
            return
    finally:
        db.close()

    await websocket.accept()
    redis = aioredis.from_url(settings.REDIS_URL)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"job:{job_id}:progress")
    try:
        # Si el job ya terminó antes de suscribirnos, emitir estado final y cerrar.
        db = SessionLocal()
        try:
            fresh = db.get(ProcessingJob, job_id)
            if fresh and fresh.status in ("completed", "failed"):
                await websocket.send_text(
                    json.dumps({"status": fresh.status, "error": fresh.error_message})
                )
                return
        finally:
            db.close()

        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message["data"]
            if isinstance(data, bytes):
                data = data.decode()
            await websocket.send_text(data)
            try:
                if json.loads(data).get("status") in ("completed", "failed"):
                    break
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"job:{job_id}:progress")
        await pubsub.aclose()
        await redis.aclose()
        try:
            await websocket.close()
        except RuntimeError:
            pass
