# Photo Restore Pro

Sistema web multiplataforma para **restauración de fotos antiguas con AI** (ComfyUI).
Sube fotos degradadas y recupéralas: elimina manchas, mejora enfoque, contraste y
resolución sin alterar rostros ni composición.

> ⚠️ **Estado:** scaffolding inicial. Solo estructura y setup básico — la lógica de
> negocio (auth, uploads, integración ComfyUI/LLM) está pendiente de implementar.

## Stack

| Capa            | Tecnología                                        |
| --------------- | ------------------------------------------------- |
| Frontend        | React 18 + Vite + TypeScript (strict) + Tailwind + shadcn/ui |
| Backend         | FastAPI (Python 3.11) + SQLAlchemy + Pydantic     |
| DB relacional   | MariaDB                                           |
| NoSQL           | MongoDB (histórico de jobs)                       |
| Cache / broker  | Redis                                             |
| Async           | Celery                                            |
| Infra           | Docker Compose                                    |

> **Red:** solo el **frontend** se publica en el host (`5273`). El resto de
> servicios (backend, MariaDB, Redis, MongoDB) viven en la red interna
> `photo-restore-network` y no exponen puertos. Un reverse proxy externo
> (fuera de este repo) asocia el frontend a un subdominio.

## Estructura

```
photo-restore-project/
├── docker-compose.yml     # Orquestación de todos los servicios
├── .env.example           # Plantilla de variables de entorno
├── backend/               # API FastAPI (app/, main.py, Dockerfile)
├── frontend/              # SPA React + Vite (único servicio expuesto)
└── volumes/               # Datos persistentes (git-ignored)
```

## Arranque rápido

```bash
# 1. Configurar entorno
cp .env.example .env        # editar valores

# 2. Levantar servicios
docker-compose build
docker-compose up -d

# 3. Verificar
docker-compose ps
# Health del backend desde dentro de la red:
docker-compose exec backend curl -s http://localhost:8000/health
```

## Acceso

| Servicio    | Acceso                                    |
| ----------- | ----------------------------------------- |
| Frontend    | http://localhost:5273 (host) → subdominio vía proxy externo |
| Backend API | interno: `http://backend:8000` (proxied en `/api` por el frontend) |
| API Docs    | interno: `http://backend:8000/docs`       |
| MariaDB     | interno: `mariadb:3306`                   |
| Redis       | interno: `redis:6379`                     |
| MongoDB     | interno: `mongodb:27017`                  |

> Para depurar un servicio interno puntualmente, añade un `ports:` temporal en
> `docker-compose.yml` o usa `docker-compose exec <servicio> ...`.

## Próximos pasos

Ver la hoja de ruta en [`docs/PHOTO_RESTORE_BRIEFING.md`](../docs/PHOTO_RESTORE_BRIEFING.md):
auth (JWT) → uploads → integración ComfyUI → LLM → dashboard → tests → deploy.
