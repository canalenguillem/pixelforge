"""Servicio de jobs de procesamiento: orquesta la restauración con ComfyUI.

Flujo (síncrono por ahora; se moverá a Celery):
    1. Crear ProcessingJob (queued) a partir de un upload propio.
    2. Subir la imagen a ComfyUI, encolar el workflow, esperar y descargar.
    3. Guardar el resultado en PROCESSED_FOLDER y actualizar el job.
"""

import os
import time
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import JobStatus, JobType
from app.models.job import ProcessingJob
from app.services import comfyui_service, upload_service, workflows
from app.utils import file_handlers
from app.utils.exceptions import AppError, NotFoundError

# Timeout de espera del resultado de ComfyUI (segundos).
_COMFYUI_JOB_TIMEOUT = 600.0


def _resolve_comfyui(user_id: int) -> tuple[str, str | None]:
    """Devuelve (server_url, api_key) de ComfyUI para el usuario.

    Por ahora usa el valor por defecto global. Cuando exista el CRUD de
    comfyui_config se leerá la config del usuario aquí.
    """
    return settings.COMFYUI_DEFAULT_URL, (settings.COMFYUI_API_KEY or None)


def enqueue_restoration(
    db: Session,
    user_id: int,
    upload_id: int,
    workflow_mode: str = "epic",
    restoration_strength: float = 0.35,
    codeformer_fidelity: float = 0.5,
    flux_denoise: float = 0.85,
    enable_hdr_lora: bool = False,
) -> ProcessingJob:
    """Crea el job (queued) y lo encola en Celery. Enruta por `workflow_mode`."""
    upload = upload_service.get_upload(db, user_id, upload_id)  # valida propiedad (404 si no)

    job = ProcessingJob(
        user_id=user_id,
        upload_id=upload.id,
        status=JobStatus.QUEUED.value,
        job_type=JobType.RESTORATION.value,
        workflow_mode=workflow_mode,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Import perezoso para evitar ciclos (tasks importa services).
    from app.workers.tasks import process_restoration_job

    process_restoration_job.delay(
        job.id,
        workflow_mode=workflow_mode,
        restoration_strength=restoration_strength,
        codeformer_fidelity=codeformer_fidelity,
        flux_denoise=flux_denoise,
        enable_hdr_lora=enable_hdr_lora,
    )
    return job


def enqueue_inpaint(
    db: Session,
    user_id: int,
    upload_id: int,
    mask_bytes: bytes,
    grow: int = 8,
) -> ProcessingJob:
    """Crea un job de inpaint (queued) con su máscara y lo encola en Celery."""
    upload = upload_service.get_upload(db, user_id, upload_id)  # valida propiedad
    mask_path = file_handlers.save_mask(user_id, mask_bytes)

    job = ProcessingJob(
        user_id=user_id,
        upload_id=upload.id,
        status=JobStatus.QUEUED.value,
        job_type=JobType.INPAINT.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.workers.tasks import process_inpaint_job

    process_inpaint_job.delay(job.id, mask_path, grow)
    return job


def get_job(db: Session, user_id: int, job_id: int) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None or job.user_id != user_id:
        raise NotFoundError("Job no encontrado")
    return job


def list_jobs(
    db: Session, user_id: int, page: int, page_size: int
) -> tuple[list[ProcessingJob], int]:
    total = (
        db.scalar(
            select(func.count()).select_from(ProcessingJob).where(ProcessingJob.user_id == user_id)
        )
        or 0
    )
    items = db.scalars(
        select(ProcessingJob)
        .where(ProcessingJob.user_id == user_id)
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def create_and_run(
    db: Session,
    user_id: int,
    upload_id: int,
    restoration_strength: float = 0.35,
    codeformer_fidelity: float = 0.5,
) -> ProcessingJob:
    """Crea un job y lo procesa de forma síncrona contra ComfyUI.

    - restoration_strength: denoise del pase de difusión (0.2 fiel .. 0.5 agresivo).
    - codeformer_fidelity: 0.0 más restauración de caras .. 1.0 más fiel.
    """
    upload = upload_service.get_upload(db, user_id, upload_id)  # valida propiedad (404 si no)

    job = ProcessingJob(
        user_id=user_id,
        upload_id=upload.id,
        status=JobStatus.QUEUED.value,
        job_type=JobType.RESTORATION.value,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    server_url, api_key = _resolve_comfyui(user_id)
    started = time.monotonic()
    try:
        job.status = JobStatus.PROCESSING.value
        db.commit()

        content = file_handlers.read_file(upload.storage_path)

        # 1) subir la imagen a ComfyUI
        uploaded = comfyui_service.upload_image(
            server_url, upload.original_filename, content, api_key
        )
        comfy_name = uploaded["name"]
        if uploaded.get("subfolder"):
            comfy_name = f"{uploaded['subfolder']}/{comfy_name}"

        # 2) encolar el workflow (dimensiones de trabajo desde las de la imagen)
        work_w, work_h = workflows.work_dimensions(
            upload.width or 1024, upload.height or 1024
        )
        workflow = workflows.build_restoration_workflow(
            comfy_name,
            work_w,
            work_h,
            denoise=restoration_strength,
            codeformer_fidelity=codeformer_fidelity,
        )
        prompt_id = comfyui_service.submit_prompt(server_url, workflow, api_key=api_key)

        # 3) esperar y descargar el resultado
        images = comfyui_service.wait_for_completion(
            server_url, prompt_id, api_key, timeout=_COMFYUI_JOB_TIMEOUT
        )
        if not images:
            raise AppError("ComfyUI no devolvió ninguna imagen de salida", 502)

        first = images[0]
        result_bytes = comfyui_service.download_image(
            server_url, first["filename"], first.get("subfolder", ""), "output", api_key
        )

        # 4) guardar y marcar completado
        extension = os.path.splitext(first["filename"])[1].lstrip(".") or "png"
        processed_path = file_handlers.save_processed(user_id, extension, result_bytes)

        job.processed_image_path = processed_path
        job.status = JobStatus.COMPLETED.value
        job.processing_time_seconds = int(time.monotonic() - started)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job

    except Exception as exc:
        job.status = JobStatus.FAILED.value
        job.error_message = str(exc)[:2000]
        job.processing_time_seconds = int(time.monotonic() - started)
        db.commit()
        db.refresh(job)
        raise


def delete_job(db: Session, user_id: int, job_id: int) -> None:
    """Elimina el resultado procesado y el registro del job."""
    job = get_job(db, user_id, job_id)
    if job.processed_image_path:
        file_handlers.delete_file(job.processed_image_path)
    db.delete(job)
    db.commit()
