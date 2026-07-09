# 📋 Photo Restore Pro - Briefing Completo para Claude Code

## 📂 Archivos Disponibles

Tienes **3 documentos de briefing** listos para enviar a Claude Code:

### 1. **PHOTO_RESTORE_BRIEFING.md** (Principal)
- ✅ Descripción general del proyecto
- ✅ Arquitectura completa (Backend + Frontend + Infraestructura)
- ✅ Stack tecnológico detallado
- ✅ Estructura de carpetas
- ✅ Modelos de BD (MariaDB + MongoDB)
- ✅ Endpoints de API
- ✅ Docker Compose completo
- ✅ Variables de entorno
- ✅ Flujo principal de restauración
- ✅ Features por usuario

**Tamaño:** ~150 KB | **Secciones:** 23

---

### 2. **TECH_IMPLEMENTATION_GUIDE.md** (Técnico)
- ✅ Ejemplos de código concretos
- ✅ Modelos SQLAlchemy con relationships
- ✅ Schemas Pydantic
- ✅ Service pattern (arquitectura)
- ✅ ComfyUI Service (integración)
- ✅ LLM Workflow Generator (OpenAI/Anthropic)
- ✅ Job Service + Celery tasks
- ✅ React hooks (useUpload)
- ✅ API service con interceptores
- ✅ Componentes React funcionales
- ✅ WebSocket monitoring
- ✅ Testing examples (pytest + React Testing)

**Tamaño:** ~120 KB | **Ejemplos de código:** 15+

---

### 3. **COMFYUI_WORKFLOWS_GUIDE.md** (Especializado)
- ✅ Cómo instalar ComfyUI + extensiones
- ✅ Modelos necesarios (GFPGAN, RealESRGAN, etc.)
- ✅ Estructura JSON de workflows
- ✅ 4 tipos de workflows listos para usar:
  - Restauración completa
  - Enhancement (contraste/colores)
  - Upscale (aumento resolución)
  - Denoise (limpieza de ruido)
- ✅ API ComfyUI (endpoints reales)
- ✅ Docker setup para ComfyUI
- ✅ Sistema de caché de workflows
- ✅ Testing de workflows
- ✅ Parámetros ajustables
- ✅ Performance tips

**Tamaño:** ~80 KB | **Workflows:** 4 completos

---

## 🚀 Cómo Usar en Claude Code

### Opción A: Uno por Uno (Recomendado para dev iterativo)

```
1. Abre Claude Code en VS Code
2. En la ventana de chat, copia y pega el contenido de:
   → PHOTO_RESTORE_BRIEFING.md
   
3. Responde al briefing principal:
   "Entendido. Crea la estructura base del proyecto con:
    - main.py en FastAPI
    - package.json base de React
    - docker-compose.yml
    - .env.example"

4. Una vez lista la base, pasa TECH_IMPLEMENTATION_GUIDE.md:
   "Ahora implementa estos servicios y modelos..."

5. Finalmente COMFYUI_WORKFLOWS_GUIDE.md:
   "Integra los workflows de ComfyUI..."
```

### Opción B: Todo de Golpe (Más rápido)

```
1. Abre Claude Code
2. En una carpeta vacía, crea archivo:
   fullbriefing.md

3. Copia los 3 documentos en orden:
   - Primero PHOTO_RESTORE_BRIEFING.md
   - Luego TECH_IMPLEMENTATION_GUIDE.md
   - Finalmente COMFYUI_WORKFLOWS_GUIDE.md

4. Envía a Claude Code:
   "Crea el proyecto completo basándote en este briefing"
```

### Opción C: Por Fases (Más control)

```
Fase 1: FOUNDATION (día 1)
├── Estructura carpetas
├── Docker Compose
├── BD MariaDB inicial
├── Redux/Zustand stores
└── API service axios

Fase 2: AUTHENTICATION (día 2)
├── JWT implementation
├── Login/Register endpoints
├── Frontend auth flow
└── Protected routes

Fase 3: UPLOADS (día 3)
├── File upload endpoint
├── Image preview
├── Validation
└── Storage management

Fase 4: COMFYUI INTEGRATION (día 4)
├── ComfyUI Service
├── Workflow generators
├── Job processing
└── WebSocket monitoring

Fase 5: UI POLISH (día 5)
├── Dashboard
├── Settings UI
├── Error handling
└── Loading states

Fase 6: DEPLOYMENT (día 6)
├── Docker multi-stage builds
├── Production env
├── Testing setup
└── Documentation
```

---

## 📝 Template de Prompts para Claude Code

### Prompt 1: Setup Inicial

```
Lee el archivo adjunto PHOTO_RESTORE_BRIEFING.md

Crea la estructura inicial del proyecto:
1. Carpetas backend/ y frontend/
2. main.py con FastAPI básico
3. package.json con React + Vite + TypeScript
4. docker-compose.yml con MariaDB, Redis, MongoDB
5. .env.example con todas las variables
6. README.md con instrucciones de setup

Usa Dockerfiles separados para backend y frontend.
NO implementes lógica aún, solo estructura.
```

### Prompt 2: Modelos y BD

```
Implementa en backend/app/models/:

1. models/user.py - User model con relationships
2. models/upload.py - Upload model
3. models/job.py - ProcessingJob model
4. models/subscription.py - UserSubscription model
5. db/base.py - Base de SQLAlchemy
6. db/init_db.py - Script inicialización BD

Usa SQLAlchemy ORM. Crea también schemas Pydantic correspondientes en app/schemas/
```

### Prompt 3: Autenticación

```
Implementa JWT authentication:

1. app/core/security.py - Hashing, JWT creation/validation
2. app/services/auth_service.py - Login, register, refresh
3. app/api/v1/endpoints/auth.py - Endpoints /register, /login, /refresh
4. Middleware JWT validation
5. Frontend: AuthStore (Zustand), LoginForm, ProtectedRoute

Usa JWT con access token (15min) + refresh token (7 días)
```

### Prompt 4: File Upload

```
Implementa sistema de uploads:

1. app/services/upload_service.py - Validación y guardado
2. app/api/v1/endpoints/uploads.py - Upload, list, delete
3. app/utils/file_handlers.py - Guardar a /volumes/uploads
4. Frontend: UploadZone (drag & drop), ImagePreview, UploadProgress

Validar: extensión, tamaño (<50MB), dimensiones
Obtener: width, height de imagen
```

### Prompt 5: ComfyUI Integration

```
Implementa ComfyUI service:

1. app/services/comfyui_service.py - Submit workflow, poll status, download
2. app/services/restoration_service.py - Orchestration
3. app/workflows/ - Workflow generators (restoration, enhancement, upscale, denoise)
4. app/api/v1/endpoints/jobs.py - Create job, get status, get result
5. WebSocket endpoint para updates en tiempo real

Ref: COMFYUI_WORKFLOWS_GUIDE.md
```

### Prompt 6: LLM Integration

```
Implementa generación de workflows con LLM:

1. app/services/llm_service.py - OpenAI, Anthropic, Grok
2. Generar workflows JSON basados en descripción
3. Manejo de API keys encriptadas
4. Fallback a workflow estático si LLM falla
5. Frontend: LLM provider selector

Soportar:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Grok (X.AI)
```

### Prompt 7: Job Processing (Celery)

```
Implementa procesamiento asincrónico:

1. app/workers/celery_app.py - Celery configuration
2. app/workers/tasks.py - Task: process_image_restoration
3. Flujo: generar workflow → submit a ComfyUI → poll → descargar → save to BD
4. Logging a MongoDB para histórico
5. Redis para caché de workflows

Usar Celery + Redis para job queue.
```

### Prompt 8: Settings UI

```
Implementa panel de configuración:

1. Backend endpoints:
   - POST /api/v1/settings/api-keys
   - GET /api/v1/settings/api-keys (masked)
   - DELETE /api/v1/settings/api-keys/{id}
   - POST /api/v1/settings/comfyui
   - GET /api/v1/settings/comfyui
   - POST /api/v1/settings/comfyui/{id}/test

2. Frontend:
   - APIKeyManager component
   - ComfyUIConfig component
   - Test connection button
   - Error/success messages

Encriptar API keys con Fernet antes de guardar.
```

### Prompt 9: Dashboard & History

```
Implementa dashboard:

1. Estadísticas:
   - Total uploads
   - Processings completados
   - Créditos usados
   - Últimas restauraciones

2. Historia de jobs:
   - Lista paginada
   - Status badges
   - Timestamps
   - Download button
   - Delete button

3. Componentes:
   - StatsCards
   - JobHistoryTable
   - BeforeAfterViewer

Backend: GET /api/v1/jobs (paginado con filters)
```

### Prompt 10: Testing & Polish

```
Finaliza con tests y optimizaciones:

1. Backend:
   - pytest para unit tests
   - tests de endpoints
   - tests de servicios
   - fixtures de BD

2. Frontend:
   - Testing Library
   - Test de componentes
   - Test de hooks
   - Test de stores

3. Polish:
   - Error boundaries
   - Loading states
   - Empty states
   - Toast notifications
   - i18n (Spanish/English)

4. Documentación:
   - API docs (FastAPI /docs)
   - README actualizado
   - Guía de dev
```

---

## 🎯 Flujo Recomendado

### Día 1: Foundation
```bash
- [ ] Estructura carpetas
- [ ] FastAPI main.py
- [ ] React + Vite setup
- [ ] Docker Compose
- [ ] BD inicial
- [ ] README desarrollo
```

### Día 2: Authentication
```bash
- [ ] User model y schema
- [ ] JWT security
- [ ] Login/register endpoints
- [ ] Auth store
- [ ] Login form
- [ ] Protected routes
- [ ] Token refresh
```

### Día 3: Upload & Preview
```bash
- [ ] Upload model
- [ ] File validation
- [ ] Upload endpoint
- [ ] Image preview
- [ ] Upload progress
- [ ] List uploads
- [ ] Delete upload
```

### Día 4: Processing Core
```bash
- [ ] Job model
- [ ] ComfyUI service
- [ ] Workflow generators (4 tipos)
- [ ] Job creation endpoint
- [ ] Status polling
- [ ] WebSocket stream
- [ ] Result download
```

### Día 5: Settings & LLM
```bash
- [ ] UserAPIKey model
- [ ] API key endpoints (encrypt/decrypt)
- [ ] ComfyUI config endpoints
- [ ] LLM service (OpenAI/Anthropic/Grok)
- [ ] Settings UI components
- [ ] Test connection endpoint
```

### Día 6: Dashboard & Polish
```bash
- [ ] Dashboard page
- [ ] Stats cards
- [ ] Job history table
- [ ] Before/after viewer
- [ ] Error handling
- [ ] Loading states
- [ ] Tests
```

### Día 7: Production
```bash
- [ ] Multi-stage Dockerfiles
- [ ] Nginx reverse proxy
- [ ] HTTPS ready
- [ ] Environment configs
- [ ] DB backups
- [ ] CI/CD setup
- [ ] Deployment docs
```

---

## 💡 Tips para Claude Code

1. **Mantener contexto:** Si una conversación se vuelve muy larga (>100 mensajes), crear nuevo chat y copiar contexto relevante.

2. **Pedidos específicos:** En lugar de "arregla el error", mostrar el error exacto y contexto.

3. **Iteración rápida:**
   ```
   "Encontré un error: [pegar error]
    Contexto: [archivo + línea]
    Mi intento: [lo que intenté]
    ¿Cómo lo arreglo?"
   ```

4. **Testing:** Después de cada feature importante:
   ```
   "Ahora crea tests para esto que acabas de implementar"
   ```

5. **Documentación:** Pedir docstrings + comentarios en código importante:
   ```
   "Agrega docstrings (Google style) a todas las funciones públicas"
   ```

---

## 🐳 Testing Local

Una vez tengas estructura base:

```bash
# En la raíz del proyecto

# Build images
docker-compose build

# Iniciar servicios
docker-compose up -d

# Verificar health
docker-compose ps

# Ver logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Pruebas
curl http://localhost:8000/docs  # API docs
curl http://localhost:5173       # Frontend

# Parar todo
docker-compose down
```

---

## 📊 Tamaño Estimado Proyecto Final

```
backend/
├── app/
│   ├── models/          ~500 líneas
│   ├── schemas/         ~600 líneas
│   ├── services/        ~2000 líneas
│   ├── api/            ~1500 líneas
│   ├── workers/        ~800 líneas
│   ├── db/             ~400 líneas
│   └── utils/          ~600 líneas
├── tests/              ~1000 líneas
└── main.py             ~200 líneas
TOTAL BACKEND: ~8000 líneas Python

frontend/
├── components/         ~2000 líneas TSX
├── pages/             ~1000 líneas TSX
├── services/          ~800 líneas TS
├── store/             ~500 líneas TS
├── hooks/             ~400 líneas TS
├── types/             ~300 líneas TS
└── utils/             ~200 líneas TS
TOTAL FRONTEND: ~5200 líneas TypeScript

Config:
├── docker-compose.yml  ~200 líneas
├── Dockerfiles        ~150 líneas
├── nginx.conf         ~100 líneas
└── Config files       ~300 líneas

TOTAL PROYECTO: ~14K líneas código
```

---

## 🔧 Cambios Último Minuto

Si necesitas cambios durante desarrollo:

```
"Cambio de requisitos: ahora ComfyUI debe ser opcional.
 Si no está disponible, usar fallback [OpenCV].
 ¿Cómo refactorizo la arquitectura?"
```

Claude Code puede sugerir:
- Patrón Strategy para procesamiento
- Servicio abstracto + implementaciones
- Feature flags en config
- Graceful degradation

---

## 📞 Si Algo Falla

```
Error: [Pegar error completo]
Archivo: [path/to/file.py]
Contexto: [5 líneas alrededor del error]
Stack trace: [si es exception]

Ya intenté: [lo que probaste]
Esperaba: [qué debería pasar]
```

---

## ✅ Checklist Final

Antes de pasar archivo a Claude Code, verifica:

- [ ] Los 3 briefings están completos
- [ ] Tienes URL de ComfyUI (local o Runpod)
- [ ] Tienes API keys para OpenAI/Anthropic/Grok (al menos una)
- [ ] Docker instalado localmente
- [ ] VS Code con Claude Code extension
- [ ] Acceso a GPU si quieres ComfyUI local (RTX 3060+ recomendado)

---

## 🎉 Ready to Go!

Copia uno de los prompts arriba y **¡empieza en Claude Code!**

El proyecto está completamente documentado. Claude Code debería poder:
- ✅ Crear estructura limpia
- ✅ Implementar cada componente
- ✅ Manejar errores gracefully
- ✅ Agregar tests automáticamente
- ✅ Documentar mientras codea

---

**Última revisión:** Julio 8, 2026  
**Estado:** Production Ready ✅  
**Estimado de desarrollo:** 5-7 días con Claude Code  
**Estimado con dev manual:** 3-4 semanas  

¡Buena suerte! 🚀
