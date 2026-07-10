"""Tareas Celery de procesamiento async (restauración de imágenes).

El progreso se publica en el canal Redis `job:{id}:progress` (pub/sub), que el
endpoint WebSocket reenvía al cliente en tiempo real.
"""

import json
import os
import time
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image

from app.core.config import settings
from app.core.constants import JobStatus
from app.db.redis_client import get_redis
from app.db.session import SessionLocal
from app.models.job import ProcessingJob
from app.models.upload import Upload
from app.services import comfyui_service, workflows
from app.utils import file_handlers
from app.workers.celery_app import celery_app


def _publish(job_id: int, payload: dict) -> None:
    get_redis().publish(f"job:{job_id}:progress", json.dumps(payload))


def _resolve_input(db, job: ProcessingJob) -> tuple[bytes, str, int, int]:
    """Devuelve (bytes, nombre, width, height) de la imagen de entrada del job.

    Si el job tiene parent_job_id, la entrada es el resultado de ese job
    (encadenado); si no, el fichero original del upload.
    """
    if job.parent_job_id:
        parent = db.get(ProcessingJob, job.parent_job_id)
        if parent is None or not parent.processed_image_path:
            raise RuntimeError("El job padre no tiene resultado disponible")
        path = parent.processed_image_path
        filename = f"job_{parent.id}.png"
    else:
        upload = db.get(Upload, job.upload_id)
        if upload is None:
            raise RuntimeError("El upload asociado no existe")
        path = upload.storage_path
        filename = upload.original_filename
    content = file_handlers.read_file(path)
    width, height = Image.open(BytesIO(content)).size
    return content, filename, width, height


# Flux es mucho más lento y su carga en frío puede tardar varios minutos.
_FLUX_TIMEOUT = 1200.0


@celery_app.task(name="process_restoration_job")
def process_restoration_job(
    job_id: int,
    workflow_mode: str = "epic",
    restoration_strength: float = 0.35,
    codeformer_fidelity: float = 0.5,
    flux_denoise: float = 0.85,
    enable_hdr_lora: bool = False,
) -> None:
    """Procesa un job de restauración contra ComfyUI, enrutando por workflow_mode."""
    db = SessionLocal()
    started = time.monotonic()
    try:
        job = db.get(ProcessingJob, job_id)
        if job is None:
            return

        server_url = settings.COMFYUI_DEFAULT_URL
        api_key = settings.COMFYUI_API_KEY or None

        job.status = JobStatus.PROCESSING.value
        db.commit()
        _publish(job_id, {"status": "processing", "stage": "uploading", "progress": 0})

        content, in_filename, in_w, in_h = _resolve_input(db, job)
        uploaded = comfyui_service.upload_image(server_url, in_filename, content, api_key)
        comfy_name = uploaded["name"]
        if uploaded.get("subfolder"):
            comfy_name = f"{uploaded['subfolder']}/{comfy_name}"

        _publish(job_id, {"status": "processing", "stage": "generating", "progress": 0})

        # Routing por modo de workflow
        timeout = 600.0
        if workflow_mode == "flux":
            workflow = workflows.build_restoration_flux_workflow(
                comfy_name, denoise=flux_denoise, enable_hdr_lora=enable_hdr_lora
            )
            timeout = _FLUX_TIMEOUT
        else:  # epic (default)
            work_w, work_h = workflows.work_dimensions(in_w or 1024, in_h or 1024)
            workflow = workflows.build_restoration_workflow(
                comfy_name, work_w, work_h,
                denoise=restoration_strength, codeformer_fidelity=codeformer_fidelity,
            )

        def on_progress(value: int, maximum: int, _node: str | None) -> None:
            pct = round(value / maximum, 3) if maximum else 0
            _publish(job_id, {"status": "processing", "stage": "generating", "progress": pct})

        images = comfyui_service.run_with_progress(
            server_url, workflow, api_key, on_progress, timeout=timeout
        )
        if not images:
            raise RuntimeError("ComfyUI no devolvió ninguna imagen")

        _publish(job_id, {"status": "processing", "stage": "downloading", "progress": 1})
        first = images[0]
        result = comfyui_service.download_image(
            server_url, first["filename"], first.get("subfolder", ""), "output", api_key
        )
        ext = os.path.splitext(first["filename"])[1].lstrip(".") or "png"
        processed_path = file_handlers.save_processed(job.user_id, ext, result)

        job.processed_image_path = processed_path
        job.status = JobStatus.COMPLETED.value
        job.processing_time_seconds = int(time.monotonic() - started)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        _publish(job_id, {"status": "completed", "job_id": job_id})

    except Exception as exc:  # noqa: BLE001 - registrar cualquier fallo en el job
        try:
            job = db.get(ProcessingJob, job_id)
            if job is not None:
                job.status = JobStatus.FAILED.value
                job.error_message = str(exc)[:2000]
                job.processing_time_seconds = int(time.monotonic() - started)
                db.commit()
        except Exception:
            pass
        _publish(job_id, {"status": "failed", "error": str(exc)[:500]})
    finally:
        db.close()


@celery_app.task(name="process_inpaint_job")
def process_inpaint_job(job_id: int, mask_path: str, grow: int = 8) -> None:
    """Elimina daño (manchas/arañazos) con LaMa sobre la zona enmascarada."""
    db = SessionLocal()
    started = time.monotonic()
    try:
        job = db.get(ProcessingJob, job_id)
        if job is None:
            return

        server_url = settings.COMFYUI_DEFAULT_URL
        api_key = settings.COMFYUI_API_KEY or None

        job.status = JobStatus.PROCESSING.value
        db.commit()
        _publish(job_id, {"status": "processing", "stage": "uploading", "progress": 0})

        img_bytes, in_filename, _in_w, _in_h = _resolve_input(db, job)
        mask_bytes = file_handlers.read_file(mask_path)
        up_img = comfyui_service.upload_image(server_url, in_filename, img_bytes, api_key)
        up_mask = comfyui_service.upload_image(server_url, "mask.png", mask_bytes, api_key, overwrite=True)
        img_name = up_img["name"]
        mask_name = up_mask["name"]
        if up_img.get("subfolder"):
            img_name = f"{up_img['subfolder']}/{img_name}"
        if up_mask.get("subfolder"):
            mask_name = f"{up_mask['subfolder']}/{mask_name}"

        _publish(job_id, {"status": "processing", "stage": "inpainting", "progress": 0})
        workflow = workflows.build_inpaint_workflow(img_name, mask_name, grow=grow)

        def on_progress(value: int, maximum: int, _node: str | None) -> None:
            pct = round(value / maximum, 3) if maximum else 0
            _publish(job_id, {"status": "processing", "stage": "inpainting", "progress": pct})

        images = comfyui_service.run_with_progress(server_url, workflow, api_key, on_progress)
        if not images:
            raise RuntimeError("ComfyUI no devolvió ninguna imagen")

        _publish(job_id, {"status": "processing", "stage": "downloading", "progress": 1})
        first = images[0]
        result = comfyui_service.download_image(
            server_url, first["filename"], first.get("subfolder", ""), "output", api_key
        )
        ext = os.path.splitext(first["filename"])[1].lstrip(".") or "png"
        processed_path = file_handlers.save_processed(job.user_id, ext, result)

        job.processed_image_path = processed_path
        job.status = JobStatus.COMPLETED.value
        job.processing_time_seconds = int(time.monotonic() - started)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        _publish(job_id, {"status": "completed", "job_id": job_id})

        file_handlers.delete_file(mask_path)  # limpiar máscara temporal

    except Exception as exc:  # noqa: BLE001
        try:
            job = db.get(ProcessingJob, job_id)
            if job is not None:
                job.status = JobStatus.FAILED.value
                job.error_message = str(exc)[:2000]
                job.processing_time_seconds = int(time.monotonic() - started)
                db.commit()
        except Exception:
            pass
        _publish(job_id, {"status": "failed", "error": str(exc)[:500]})
    finally:
        db.close()
