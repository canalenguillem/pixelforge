"""Servicio de jobs de procesamiento: orquesta la restauración con ComfyUI.

Flujo (síncrono por ahora; se moverá a Celery):
    1. Crear ProcessingJob (queued) a partir de un upload propio.
    2. Subir la imagen a ComfyUI, encolar el workflow, esperar y descargar.
    3. Guardar el resultado en PROCESSED_FOLDER y actualizar el job.
"""

import os
import time
from datetime import datetime, timezone

from sqlalchemy import func, select, update
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


def _resolve_root_upload(
    db: Session, user_id: int, upload_id: int, parent_job_id: int | None
) -> int:
    """Valida el origen y devuelve el upload raíz.

    Si hay parent_job_id, la entrada será el resultado de ese job (encadenado);
    el upload raíz se hereda del padre para agrupar toda la cadena.
    """
    if parent_job_id is not None:
        parent = db.get(ProcessingJob, parent_job_id)
        if parent is None or parent.user_id != user_id:
            raise NotFoundError("Job padre no encontrado")
        if parent.status != JobStatus.COMPLETED.value or not parent.processed_image_path:
            raise AppError("El job padre no tiene un resultado disponible", 409)
        return parent.upload_id
    upload = upload_service.get_upload(db, user_id, upload_id)  # valida propiedad (404 si no)
    return upload.id


def enqueue_restoration(
    db: Session,
    user_id: int,
    upload_id: int,
    parent_job_id: int | None = None,
    workflow_mode: str = "epic",
    restoration_strength: float = 0.35,
    codeformer_fidelity: float = 0.5,
    flux_denoise: float = 1.0,
    enable_hdr_lora: bool = False,
    colorize: bool = False,
) -> ProcessingJob:
    """Crea el job (queued) y lo encola en Celery. Enruta por `workflow_mode`."""
    root_upload_id = _resolve_root_upload(db, user_id, upload_id, parent_job_id)

    if workflow_mode == "flux":
        params: dict = {
            "flux_denoise": flux_denoise,
            "enable_hdr_lora": enable_hdr_lora,
            "colorize": colorize,
        }
    else:
        params = {"restoration_strength": restoration_strength, "codeformer_fidelity": codeformer_fidelity}

    job = ProcessingJob(
        user_id=user_id,
        upload_id=root_upload_id,
        parent_job_id=parent_job_id,
        status=JobStatus.QUEUED.value,
        job_type=JobType.RESTORATION.value,
        workflow_mode=workflow_mode,
        params=params,
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
        colorize=colorize,
    )
    return job


def enqueue_inpaint(
    db: Session,
    user_id: int,
    upload_id: int,
    mask_bytes: bytes,
    grow: int = 8,
    parent_job_id: int | None = None,
) -> ProcessingJob:
    """Crea un job de inpaint (queued) con su máscara y lo encola en Celery."""
    root_upload_id = _resolve_root_upload(db, user_id, upload_id, parent_job_id)
    mask_path = file_handlers.save_mask(user_id, mask_bytes)

    job = ProcessingJob(
        user_id=user_id,
        upload_id=root_upload_id,
        parent_job_id=parent_job_id,
        status=JobStatus.QUEUED.value,
        job_type=JobType.INPAINT.value,
        params={"grow": grow},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.workers.tasks import process_inpaint_job

    process_inpaint_job.delay(job.id, mask_path, grow)
    return job


def enqueue_style(
    db: Session,
    user_id: int,
    upload_id: int,
    style: str,
    strength: float = 0.5,
    parent_job_id: int | None = None,
) -> ProcessingJob:
    """Crea un job de estilo (Z-Image img2img) y lo encola en Celery."""
    root_upload_id = _resolve_root_upload(db, user_id, upload_id, parent_job_id)

    job = ProcessingJob(
        user_id=user_id,
        upload_id=root_upload_id,
        parent_job_id=parent_job_id,
        status=JobStatus.QUEUED.value,
        job_type=JobType.STYLE.value,
        params={"style": style, "strength": strength},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.workers.tasks import process_style_job

    process_style_job.delay(job.id, style, strength)
    return job


def get_job(db: Session, user_id: int, job_id: int) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None or job.user_id != user_id:
        raise NotFoundError("Job no encontrado")
    return job


def list_jobs(
    db: Session,
    user_id: int,
    page: int,
    page_size: int,
    upload_id: int | None = None,
) -> tuple[list[ProcessingJob], int]:
    filters = [ProcessingJob.user_id == user_id]
    if upload_id is not None:
        filters.append(ProcessingJob.upload_id == upload_id)

    total = db.scalar(select(func.count()).select_from(ProcessingJob).where(*filters)) or 0
    # Para la galería (filtrada por upload) queremos orden cronológico ascendente
    # para reconstruir la cadena; el listado global va descendente.
    order = (
        (ProcessingJob.created_at.asc(), ProcessingJob.id.asc())
        if upload_id is not None
        else (ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    )
    items = db.scalars(
        select(ProcessingJob)
        .where(*filters)
        .order_by(*order)
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
    """Elimina el resultado procesado y el registro del job.

    Los jobs encadenados a partir de este (hijos) quedan huérfanos: se les pone
    parent_job_id a NULL para no dejar referencias colgando.
    """
    job = get_job(db, user_id, job_id)
    db.execute(
        update(ProcessingJob)
        .where(ProcessingJob.parent_job_id == job_id)
        .values(parent_job_id=None)
    )
    if job.processed_image_path:
        file_handlers.delete_file(job.processed_image_path)
    db.delete(job)
    db.commit()
