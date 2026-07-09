# ==============================================================================
# Photo Restore Pro - Backend Dockerfile
# ==============================================================================
# Imagen de DESARROLLO (usada por docker-compose con --reload).
# La configuración multi-stage para PRODUCCIÓN está más abajo, comentada.
# ==============================================================================

FROM python:3.11-slim

# Evita .pyc y buffering de stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias de sistema (OpenCV, Pillow, mysqlclient/pymysql, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        default-libmysqlclient-dev \
        pkg-config \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python primero (mejor cache de capas)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código (en dev el volumen de docker-compose lo sobrescribe)
COPY . .

# Carpetas de storage
RUN mkdir -p /app/uploads /app/processed /app/logs

EXPOSE 8000

# Comando por defecto (docker-compose lo sobrescribe con --reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# ==============================================================================
# PRODUCCIÓN - Multi-stage build (descomentar y reemplazar el bloque de arriba)
# ==============================================================================
#
# ---- Stage 1: builder -------------------------------------------------------
# FROM python:3.11-slim AS builder
#
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     PIP_NO_CACHE_DIR=1
#
# WORKDIR /app
#
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         build-essential default-libmysqlclient-dev pkg-config \
#     && rm -rf /var/lib/apt/lists/*
#
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
#
# ---- Stage 2: runtime -------------------------------------------------------
# FROM python:3.11-slim AS runtime
#
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1
#
# WORKDIR /app
#
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         libgl1 libglib2.0-0 curl \
#     && rm -rf /var/lib/apt/lists/*
#
# # Usuario no-root
# RUN addgroup --system app && adduser --system --ingroup app app
#
# COPY --from=builder /wheels /wheels
# COPY requirements.txt .
# RUN pip install --no-cache /wheels/*
#
# COPY . .
# RUN mkdir -p /app/uploads /app/processed /app/logs && chown -R app:app /app
#
# USER app
# EXPOSE 8000
#
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1
#
# # Gunicorn + Uvicorn workers para producción
# CMD ["gunicorn", "main:app", \
#      "-k", "uvicorn.workers.UvicornWorker", \
#      "--bind", "0.0.0.0:8000", \
#      "--workers", "4"]
# ==============================================================================
