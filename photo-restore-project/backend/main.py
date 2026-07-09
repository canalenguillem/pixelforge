"""Photo Restore Pro - FastAPI application entrypoint.

Inicializa la app, configura CORS, monta el router de la API v1 y expone
un health check. La lógica de negocio vive en `app/` (services, models, etc.).
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.utils.exceptions import AppError

# Importa los modelos para registrarlos en el metadata de SQLAlchemy
# (resuelve las relaciones User <-> UserSubscription).
import app.models  # noqa: F401,E402

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0-alpha",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Exception handlers
# -----------------------------------------------------------------------------
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Traduce errores de dominio (AppError) a respuestas JSON con su código HTTP."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# -----------------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness/health endpoint usado por Docker y el reverse proxy."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Endpoint raíz — puntero a la documentación."""
    return {"message": f"{settings.PROJECT_NAME} API", "docs": "/docs"}
