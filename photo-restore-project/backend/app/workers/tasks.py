"""Tareas Celery de procesamiento async (restauración de imágenes).

Placeholder inicial — sin tareas implementadas todavía.
"""

# from app.workers.celery_app import celery_app
#
# TODO: @celery_app.task  process_restoration_job(job_id: int) -> None
#   1. Cargar upload + params
#   2. Generar workflow con LLM
#   3. Enviar a ComfyUI y hacer polling
#   4. Descargar resultado y guardar en PROCESSED_FOLDER
#   5. Actualizar estado del job + histórico en MongoDB
