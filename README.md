# PixelForge

Restauración de fotos antiguas con IA (ComfyUI). Sube fotos degradadas y
recupéralas: reenfoca, limpia grano y restaura rostros sin alterar la
composición original.

## Stack

- **Frontend**: React 18 + Vite + TypeScript (strict) + TailwindCSS + shadcn/ui
- **Backend**: FastAPI (Python 3.11) + SQLAlchemy + Pydantic
- **Datos**: MariaDB (relacional) · MongoDB (histórico) · Redis (cache/colas)
- **Async**: Celery
- **IA**: ComfyUI externo (Tile ControlNet + CodeFormer + RealESRGAN)
- **Infra**: Docker Compose

## Estructura

```
pixelforge/
├── docs/                    # Briefing y documentación de diseño
└── photo-restore-project/   # Aplicación (backend, frontend, docker-compose)
```

## Arranque rápido

```bash
cd photo-restore-project
cp .env.example .env          # editar valores
docker compose up -d
```

Solo el frontend se publica al host (puerto `5273`); el resto de servicios
viven en la red interna de Docker. Ver
[`photo-restore-project/README.md`](photo-restore-project/README.md) para detalles.

## Estado

En desarrollo. Implementado: scaffolding completo, auth (JWT), uploads,
e integración con ComfyUI (restauración fiel de punta a punta).
