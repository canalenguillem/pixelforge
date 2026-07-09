"""Configuración de Celery (usa Redis como broker y backend de resultados).

Placeholder inicial — la instancia está creada pero sin tareas registradas.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "photo_restore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
