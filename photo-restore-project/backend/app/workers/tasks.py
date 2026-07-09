"""Tareas Celery de procesamiento async (restauración de imágenes).

El progreso se publica en el canal Redis `job:{id}:progress` (pub/sub), que el
endpoint WebSocket reenvía al cliente en tiempo real.
"""

import json
import os
import time
from datetime import datetime, timezone

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


@celery_app.task(name="process_restoration_job")
def process_restoration_job(
    job_id: int,
    restoration_strength: float = 0.35,
    codeformer_fidelity: float = 0.5,
) -> None:
    """Procesa un job de restauración contra ComfyUI, publicando progreso."""
    db = SessionLocal()
    started = time.monotonic()
    try:
        job = db.get(ProcessingJob, job_id)
        if job is None:
            return
        upload = db.get(Upload, job.upload_id)
        if upload is None:
            raise RuntimeError("El upload asociado no existe")

        server_url = settings.COMFYUI_DEFAULT_URL
        api_key = settings.COMFYUI_API_KEY or None

        job.status = JobStatus.PROCESSING.value
        db.commit()
        _publish(job_id, {"status": "processing", "stage": "uploading", "progress": 0})

        content = file_handlers.read_file(upload.storage_path)
        uploaded = comfyui_service.upload_image(
            server_url, upload.original_filename, content, api_key
        )
        comfy_name = uploaded["name"]
        if uploaded.get("subfolder"):
            comfy_name = f"{uploaded['subfolder']}/{comfy_name}"

        _publish(job_id, {"status": "processing", "stage": "generating", "progress": 0})

        work_w, work_h = workflows.work_dimensions(upload.width or 1024, upload.height or 1024)
        workflow = workflows.build_restoration_workflow(
            comfy_name, work_w, work_h,
            denoise=restoration_strength, codeformer_fidelity=codeformer_fidelity,
        )

        def on_progress(value: int, maximum: int, _node: str | None) -> None:
            pct = round(value / maximum, 3) if maximum else 0
            _publish(job_id, {"status": "processing", "stage": "generating", "progress": pct})

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
