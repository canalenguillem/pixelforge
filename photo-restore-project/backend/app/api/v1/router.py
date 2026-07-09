"""Agregación de routers de la API v1.

Reúne todos los routers de `endpoints/` bajo un único APIRouter que main.py
monta con el prefijo /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, jobs, settings, uploads, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
