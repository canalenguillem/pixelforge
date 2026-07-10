# PixelForge — Estado del proyecto (handoff)

> Documento de traspaso para retomar el desarrollo. Última actualización: **2026-07-10**.
> Repo: https://github.com/canalenguillem/pixelforge · Rama: `main`

Restaurador de fotos antiguas con IA (ComfyUI). Backend FastAPI + frontend React/Vite,
todo en Docker Compose. **Funciona de punta a punta**: login → subir → restaurar / quitar
manchas → comparar antes/después → descargar, con procesamiento asíncrono y progreso en vivo.

---

## 1. Lo que está IMPLEMENTADO y probado

| Área | Estado | Notas |
|------|--------|-------|
| Scaffolding (backend/frontend/compose/BDs) | ✅ | 6 servicios healthy |
| Auth JWT | ✅ | register, login, refresh, logout (revocación en Redis), `/me` |
| Uploads | ✅ | multipart, validación (ext+tamaño+imagen real con Pillow), storage, aislamiento por usuario |
| Restauración ComfyUI | ✅ | difusión img2img + **Tile ControlNet** + **CodeFormer** (caras) + RealESRGAN x2 |
| Inpainting (quitar manchas) | ✅ | **LaMa** (`big-lama`), rellena solo lo enmascarado, resto pixel-idéntico |
| Async (Celery + WebSocket) | ✅ | `POST /jobs` responde 202; progreso real del sampler vía WS de ComfyUI → Redis pub/sub → WS al cliente |
| Frontend completo | ✅ | login/registro, drag&drop, sliders, **editor de máscara con pincel**, visor antes/después, barra de progreso |

### Estado en git
- `0f00796` base · `e5d880b` frontend · `eab1add` async (**último pusheado**)
- ⚠️ **La feature de inpainting está construida pero SIN commitear** (backend + frontend). Falta `git add/commit/push`.

---

## 2. Arquitectura y stack

```
Navegador ──5273──> Frontend (Vite dev) ──/api proxy──> Backend (FastAPI :8000)
                                                          ├─ MariaDB (usuarios/uploads/jobs)
                                                          ├─ Redis (cache, colas Celery, pub/sub progreso)
                                                          ├─ MongoDB (histórico jobs — NO usado aún)
                                                          └─ Celery worker ──HTTP/WS──> ComfyUI (externo)
```

- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic v2, `bcrypt` directo (NO passlib), python-jose, httpx, websockets, Celery.
- **Frontend**: React 18 + Vite 6 + TS strict + Tailwind + shadcn tokens; axios, zustand (persist), react-dropzone, lucide-react. **Sin radix/shadcn components instalados** (UI hecha a mano con Tailwind).
- **IA**: ComfyUI externo (no en Docker).

---

## 3. ⚠️ Cosas críticas / no obvias (LEER antes de tocar)

1. **ComfyUI es EXTERNO y puede estar APAGADO.**
   - Máquina: **Windows 11 en `192.168.1.46`**, RTX 4060 Ti (16 GB), ComfyUI 0.21.0 nativo (no Docker).
   - Se lanza con `D:\AI\ComfyUI\start.bat` → `python main.py --listen 0.0.0.0 --port 8188`.
   - **Antes de trabajar con jobs, verifica que responde**: `curl -m5 http://192.168.1.46:8188/system_stats`. Si no, pide al usuario que la encienda.
   - Acceso SSH sin password: `ssh guillem@192.168.1.46` (shell = cmd de Windows; usar PowerShell para descargas grandes de GitHub, `curl` de Windows falla con release-assets por Schannel).

2. **La CPU del host Docker NO tiene AVX** → MongoDB está fijado a `mongo:4.4` (la 5+ crashea con "Illegal instruction"). No subir la versión. Healthcheck usa `mongo` (no `mongosh`).

3. **Red Docker**: SOLO el frontend expone puerto al host (**`5273:5173`**, el 5173 estaba ocupado). Backend/BDs sin puertos publicados; se hablan por la red interna `photo-restore-network`. El proxy de Vite reenvía `/api` (con `ws:true`) a `backend:8000`.

4. **Secretos / .env**:
   - `.env` y `backend/.env` NO se commitean (gitignored). `COMFYUI_DEFAULT_URL` en el `.env` local = `http://192.168.1.46:8188` (IP real). En `.env.example` y `config.py` el default es `http://host.docker.internal:8188` (genérico, sin exponer la IP).
   - `foto_test/` y `volumes/` también gitignored (fotos personales).

5. **Hot-reload**:
   - Backend: uvicorn `--reload` recoge cambios de código al vuelo.
   - **Celery NO hot-reloadea**: tras tocar `workers/tasks.py` → `docker compose restart celery-worker`.
   - Frontend: solo están montados `src/`, `public/`, `index.html`. **`vite.config.ts`, `tsconfig.json`, `package.json` NO están montados** → si los cambias, `docker compose cp` al contenedor + restart, o rebuild.
   - Cambiar `.env` requiere `docker compose up -d --force-recreate <servicio>` (restart NO relee env_file).

6. **Usuario de prueba**: `ana@example.com` / `supersecret123` (también existe `bob@example.com` / `supersecret123`).

---

## 4. Modelos instalados en ComfyUI (por SSH)

| Modelo | Ruta en la máquina Windows | Uso |
|--------|----------------------------|-----|
| `control_v11f1e_sd15_tile_fp16.safetensors` | `models\controlnet\SD1.5\` | Tile ControlNet (restauración fiel) |
| `codeformer.pth` | `models\facerestore_models\` | Restauración de caras |
| `detection_Resnet50_Final.pth`, `parsing_parsenet.pth` | `models\facedetection\` | Detección/parsing de caras (facerestore_cf) |
| `big-lama.pt` | `models\inpaint\` | Inpainting (quitar manchas) |
| Checkpoints: `epicrealism.safetensors` (usado), absolutereality, v1-5-pruned | `models\checkpoints\` | img2img de restauración |
| `RealESRGAN_x2.pth` | `models\upscale_models\` | Upscale x2 |

Custom node añadido: **`facerestore_cf`** (en `custom_nodes\`, deps instaladas en su venv). El pack `comfyui-inpaint-nodes` ya estaba.

---

## 5. Pipelines de ComfyUI (en `backend/app/services/workflows.py`)

**Restauración** (`build_restoration_workflow`): escala a lado largo 1024 → img2img con epicrealism guiado por Tile ControlNet a `denoise` (param **restoration_strength**, 0.2 fiel .. 0.5 agresivo, default 0.35) → RealESRGAN x2 → CodeFormer.
- Aprendizaje clave: el salto de calidad vino de la **difusión+tile**, no del upscaler. Tradeoff: denoise alto quita más manchas pero altera identidad; 0.35 es el equilibrio fiel.

**Inpainting** (`build_inpaint_workflow`): LaMa (`INPAINT_InpaintWithModel`) sobre la máscara (blanco=reparar, `GrowMask` +8px) → `ImageCompositeMasked` sobre el original.
- Garantía: lo NO enmascarado queda idéntico (verificado, diff≈0). LaMa no alucina.
- **Idea pendiente**: encadenar inpaint → restauración en un solo flujo.

---

## 6. API (prefijo `/api/v1`)

```
POST   /auth/register · /auth/login · /auth/refresh · /auth/logout    GET /auth/me
POST   /uploads (multipart)   GET /uploads   GET /uploads/{id}   DELETE /uploads/{id}   GET /uploads/{id}/download
POST   /jobs               {upload_id, restoration_strength, codeformer_fidelity}  -> 202 (async)
POST   /jobs/inpaint       multipart {upload_id, mask, grow}                        -> 202 (async)
GET    /jobs   GET /jobs/{id}   GET /jobs/{id}/result   DELETE /jobs/{id}
WS     /jobs/{id}/stream?token=<jwt>    progreso en tiempo real (pub/sub Redis)
```
Jobs son síncronos-a-nivel-lógico dentro de Celery; el cliente hace `POST` (202) → WS/polling → `GET /result` (blob).

---

## 7. Cómo trabajar / probar (patrones útiles)

```bash
cd photo-restore-project
docker compose ps                       # estado
docker compose logs -f backend|celery-worker|frontend

# Ejecutar un script Python dentro del backend (tiene httpx, PIL, acceso a ComfyUI y a la app):
docker compose exec -T backend python < mi_script.py

# Meter/sacar ficheros del contenedor:
docker compose cp foto.jpg backend:/tmp/foto.jpg
docker compose cp backend:/tmp/out.png ./out.png

# Resultados procesados (montado en el host):
ls volumes/processed/user_<id>/

# Probar la API desde dentro (backend no expone puerto):
docker compose exec -T backend curl -s http://localhost:8000/health
# O desde el host por el proxy de Vite:
curl http://localhost:5273/api/v1/...
```

Para iterar sobre workflows de ComfyUI: hay scripts de referencia usados durante el desarrollo
(en el scratchpad de la sesión, no en el repo): subían imagen a ComfyUI, montaban el workflow,
hacían polling y descargaban el resultado. El módulo `comfyui_service` expone los primitivos
(`upload_image`, `submit_prompt`, `run_with_progress`, `download_image`, `check_connection`).

---

## 8. Estructura relevante del backend

```
backend/app/
├── core/            config.py (pydantic-settings), security.py (bcrypt+JWT), constants.py
├── db/              session.py (MariaDB), redis_client.py, base.py
├── models/          user, subscription, upload, job  (mapeados a backend/sql/init.sql)
├── schemas/         user, auth, upload, job
├── services/        auth_service, user_service, upload_service, job_service,
│                    comfyui_service, image_service, workflows
├── workers/         celery_app.py, tasks.py  (process_restoration_job, process_inpaint_job)
├── api/deps.py      (get_current_user, DbSession)
└── api/v1/endpoints/ auth, users, uploads, jobs (+ WS), settings
```
Frontend: `src/{pages,components/{Auth,Upload,Editor,Layout},services,store,types}`.

---

## 9. Próximos pasos (roadmap sugerido)

1. **Commitear + pushear la feature de inpainting** (pendiente).
2. **Histórico en MongoDB** (`jobs_history`): guardar workflow/respuesta/metadatos por job. Motor/pymongo ya en requirements; falta el cliente Mongo y escribir en el flujo.
3. **Config ComfyUI por usuario**: usar la tabla `comfyui_config` (ya en el schema) en `job_service._resolve_comfyui` en vez del default global. Ídem API keys de LLM (`user_api_keys`, encriptar con Fernet — `ENCRYPTION_KEY` en env).
4. **Encadenar inpaint → restauración** en un solo job.
5. **Pulir UI**: header/sidebar, galería de jobs anteriores (`GET /jobs`), página de ajustes.
6. **Endpoints stub sin implementar**: `users` (perfil/password/cuenta), `settings` (api-keys, comfyui config + test). Celery: mover polling a algo más fino si hace falta.
7. **Producción**: Dockerfiles multi-stage (ya comentados en los Dockerfile), usuario no-root (ahora los ficheros se crean como root en los volúmenes), HTTPS lo pone el reverse proxy externo del usuario (subdominio).

---

## 10. Contexto del usuario

- Trabaja en español. Tiene "2000 servicios" en la máquina host → cuidado con puertos (por eso solo el 5273).
- Tiene un reverse proxy en su red doméstica que expone el frontend por un subdominio (no montar nginx aquí).
- ComfyUI en máquina aparte (192.168.1.46); la apaga/enciende — verificar conectividad antes de jobs.
