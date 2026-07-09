# Photo Restore Pro - Proyecto Completo

## 📋 Descripción General

Sistema web multiplataforma para restauración de fotos antiguas usando AI (ComfyUI). Permite a usuarios subir fotos degradadas y restaurarlas removiendo manchas, mejorando enfoque, contraste y calidad de impresión, sin alterar rostros ni composición original.

**Características principales:**
- Autenticación multi-usuario con JWT
- Configuración personal de API keys (OpenAI, Anthropic, Grok, etc.)
- Servidor ComfyUI personalizado (local o RemotePC/Runpod)
- Gestión de historiales de procesamiento
- Descarga de fotos restauradas en alta resolución
- Dashboard con estadísticas de uso
- Sistema de créditos/cuotas por usuario

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│  Frontend Vite  │
│  React + TS     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI       │
│  Backend       │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬────────┐
    ▼         ▼          ▼        ▼
┌────────┐ ┌─────┐ ┌───────┐ ┌──────────┐
│MariaDB │ │Redis│ │MongoDB│ │ ComfyUI  │
│  Datos │ │Cache│ │  Jobs │ │(External)│
└────────┘ └─────┘ └───────┘ └──────────┘
```

---

## 🔧 Stack Tecnológico

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Auth:** JWT + SQLAlchemy ORM
- **DB Relacional:** MariaDB
- **NoSQL:** MongoDB (histórico de jobs/resultados)
- **Cache:** Redis (sesiones, rate limiting)
- **Integraciones:** OpenAI API, Anthropic API, Grok API
- **Task Queue:** Celery + Redis (procesamiento async)
- **Imagen:** Pillow, OpenCV (preprocessing)

### Frontend
- **Framework:** React 18 + Vite
- **TypeScript:** Strict mode
- **Estado:** Zustand o Redux Toolkit
- **HTTP:** Axios + interceptores
- **UI:** Shadcn/UI + TailwindCSS
- **Drag & Drop:** React-dropzone
- **Progreso:** WebSockets para updates en tiempo real

### Infraestructura
- **Containerización:** Docker + Docker Compose
- **Orquestación:** Docker Compose (no Kubernetes para dev local)
- **Volúmenes:** Para persistencia de datos y uploads

---

## 📁 Estructura del Proyecto

```
photo-restore-project/
├── docker-compose.yml          # Orquestación de servicios
├── .env.example                # Variables de entorno
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # App FastAPI
│   ├── .env
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── config.py       # Configuración (env vars)
│   │   │   ├── security.py     # JWT, hashing
│   │   │   └── constants.py    # Constantes (limites, etc)
│   │   │
│   │   ├── db/
│   │   │   ├── base.py         # Base SQLAlchemy
│   │   │   ├── session.py      # DB session factory
│   │   │   ├── init_db.py      # Inicialización
│   │   │   └── redis_client.py # Redis connection pool
│   │   │
│   │   ├── models/
│   │   │   ├── user.py         # User model
│   │   │   ├── upload.py       # Upload/Photo model
│   │   │   ├── job.py          # Processing job model
│   │   │   └── subscription.py # Plan/credits model
│   │   │
│   │   ├── schemas/
│   │   │   ├── user.py         # Pydantic schemas
│   │   │   ├── upload.py
│   │   │   ├── job.py
│   │   │   └── auth.py
│   │   │
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py      # Login, register, refresh
│   │   │   │   │   ├── users.py     # Profile, settings
│   │   │   │   │   ├── uploads.py   # Upload, list, delete
│   │   │   │   │   ├── jobs.py      # Process, status, results
│   │   │   │   │   └── settings.py  # API keys, ComfyUI config
│   │   │   │   └── router.py    # API router aggregation
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py      # Autenticación
│   │   │   ├── user_service.py      # CRUD usuarios
│   │   │   ├── upload_service.py    # Gestión uploads
│   │   │   ├── comfyui_service.py   # Integración ComfyUI
│   │   │   ├── llm_service.py       # OpenAI/Anthropic/Grok
│   │   │   ├── image_service.py     # Procesamiento imágenes
│   │   │   └── job_service.py       # Gestión jobs
│   │   │
│   │   ├── workers/
│   │   │   ├── celery_app.py        # Celery config
│   │   │   └── tasks.py             # Celery tasks
│   │   │
│   │   ├── utils/
│   │   │   ├── validators.py        # Validadores
│   │   │   ├── file_handlers.py     # Upload/download
│   │   │   ├── logger.py            # Logging
│   │   │   └── exceptions.py        # Custom exceptions
│   │   │
│   │   └── middleware/
│   │       ├── cors.py
│   │       ├── rate_limit.py
│   │       └── error_handler.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_uploads.py
│       └── test_comfyui.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   │
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   │
│   │   │   ├── Auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   │
│   │   │   ├── Upload/
│   │   │   │   ├── UploadZone.tsx
│   │   │   │   ├── ImagePreview.tsx
│   │   │   │   └── UploadProgress.tsx
│   │   │   │
│   │   │   ├── Editor/
│   │   │   │   ├── BeforeAfterViewer.tsx
│   │   │   │   ├── ProcessingOptions.tsx
│   │   │   │   └── ResultViewer.tsx
│   │   │   │
│   │   │   ├── Settings/
│   │   │   │   ├── APIKeyManager.tsx
│   │   │   │   ├── ComfyUIConfig.tsx
│   │   │   │   └── UserProfile.tsx
│   │   │   │
│   │   │   ├── Dashboard/
│   │   │   │   ├── Stats.tsx
│   │   │   │   ├── RecentUploads.tsx
│   │   │   │   └── JobHistory.tsx
│   │   │   │
│   │   │   └── Common/
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       └── Toast.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── EditorPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts             # Axios instance
│   │   │   ├── auth.service.ts
│   │   │   ├── upload.service.ts
│   │   │   ├── job.service.ts
│   │   │   └── websocket.service.ts
│   │   │
│   │   ├── store/
│   │   │   ├── authStore.ts       # Zustand store
│   │   │   ├── uploadStore.ts
│   │   │   └── settingsStore.ts
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useUpload.ts
│   │   │   └── useWebSocket.ts
│   │   │
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── user.ts
│   │   │   ├── upload.ts
│   │   │   └── job.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── api.utils.ts
│   │   │   ├── file.utils.ts
│   │   │   └── format.utils.ts
│   │   │
│   │   ├── constants/
│   │   │   ├── api.constants.ts
│   │   │   └── ui.constants.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   └── public/
│       └── favicon.svg
│
└── nginx/
    ├── Dockerfile
    └── nginx.conf              # Config para reverse proxy
```

---

## 🗄️ Modelos de Base de Datos

### MariaDB

#### users
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_email (email)
);
```

#### user_api_keys
```sql
CREATE TABLE user_api_keys (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    provider VARCHAR(50) NOT NULL, -- 'openai', 'anthropic', 'grok'
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_provider (user_id, provider),
    INDEX idx_user_id (user_id)
);
```

#### comfyui_config
```sql
CREATE TABLE comfyui_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    server_url VARCHAR(500) NOT NULL, -- http://localhost:8188 o Runpod
    api_key VARCHAR(255),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);
```

#### uploads
```sql
CREATE TABLE uploads (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    width INT,
    height INT,
    status VARCHAR(50) DEFAULT 'uploaded', -- 'uploaded', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

#### processing_jobs
```sql
CREATE TABLE processing_jobs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    upload_id BIGINT NOT NULL,
    status VARCHAR(50) DEFAULT 'queued', -- 'queued', 'processing', 'completed', 'failed'
    job_type VARCHAR(100), -- 'restoration', 'enhancement', 'upscale'
    processed_image_path VARCHAR(1000),
    error_message TEXT,
    processing_time_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

#### user_subscriptions
```sql
CREATE TABLE user_subscriptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    plan_type VARCHAR(50) DEFAULT 'free', -- 'free', 'pro', 'enterprise'
    credits_balance INT DEFAULT 100,
    credits_used INT DEFAULT 0,
    monthly_uploads_limit INT DEFAULT 10,
    uploads_used INT DEFAULT 0,
    api_rate_limit INT DEFAULT 100, -- req/hour
    is_active BOOLEAN DEFAULT TRUE,
    renewal_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);
```

### MongoDB

#### jobs_history
```javascript
{
    _id: ObjectId,
    user_id: Long,
    upload_id: Long,
    job_id: Long,
    comfyui_workflow: Object, // JSON del workflow enviado a ComfyUI
    comfyui_response: Object, // Respuesta de ComfyUI
    processing_metadata: {
        llm_used: String, // 'openai', 'anthropic', 'grok'
        prompt: String,
        model: String,
        tokens_used: Int
    },
    before_image_url: String,
    after_image_url: String,
    processing_time_ms: Int,
    status: String,
    created_at: Date,
    completed_at: Date
}
```

---

## 🔌 API Endpoints

### Auth
```
POST   /api/v1/auth/register          - Registro
POST   /api/v1/auth/login             - Login
POST   /api/v1/auth/refresh           - Refresh token
POST   /api/v1/auth/logout            - Logout
GET    /api/v1/auth/me                - Info usuario actual
```

### Users
```
GET    /api/v1/users/profile          - Perfil del usuario
PUT    /api/v1/users/profile          - Actualizar perfil
PUT    /api/v1/users/password         - Cambiar contraseña
DELETE /api/v1/users/account          - Eliminar cuenta
```

### Uploads
```
POST   /api/v1/uploads                - Subir foto (multipart/form-data)
GET    /api/v1/uploads                - Listar uploads (paginado)
GET    /api/v1/uploads/{id}           - Detalles de un upload
DELETE /api/v1/uploads/{id}           - Eliminar upload
GET    /api/v1/uploads/{id}/download  - Descargar original
```

### Jobs (Procesamiento)
```
POST   /api/v1/jobs                   - Crear job de procesamiento
GET    /api/v1/jobs                   - Listar jobs del usuario
GET    /api/v1/jobs/{id}              - Estado de un job
GET    /api/v1/jobs/{id}/result       - Descargar resultado
DELETE /api/v1/jobs/{id}              - Cancelar job
GET    /api/v1/jobs/{id}/stream       - WebSocket para updates
```

### Settings
```
POST   /api/v1/settings/api-keys      - Guardar API key
GET    /api/v1/settings/api-keys      - Listar API keys (masked)
DELETE /api/v1/settings/api-keys/{id} - Eliminar API key

POST   /api/v1/settings/comfyui       - Configurar ComfyUI
GET    /api/v1/settings/comfyui       - Obtener config
PUT    /api/v1/settings/comfyui/{id}  - Actualizar config
DELETE /api/v1/settings/comfyui/{id}  - Eliminar config
POST   /api/v1/settings/comfyui/{id}/test - Probar conexión
```

### Admin
```
GET    /api/v1/admin/stats            - Estadísticas globales
GET    /api/v1/admin/users            - Listar usuarios
PUT    /api/v1/admin/users/{id}       - Moderar usuario
```

---

## 🔐 Seguridad

- **JWT:** Access token (15 min) + Refresh token (7 días)
- **Encriptación:** API keys encriptadas en BD con Fernet (cryptography)
- **CORS:** Configurado para localhost en dev, dominio en prod
- **Rate Limiting:** Redis-backed (100 req/min por IP)
- **HTTPS:** Nginx con certificados (self-signed en dev)
- **Validación:** Pydantic models con tipos estrictos
- **SQL Injection:** ORM SQLAlchemy (no raw queries)

---

## 🐳 Docker Compose

```yaml
version: '3.8'

services:
  mariadb:
    image: mariadb:latest
    container_name: photo-restore-db
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./volumes/mariadb:/var/lib/mysql
      - ./backend/sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"
    networks:
      - photo-restore-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: photo-restore-cache
    volumes:
      - ./volumes/redis:/data
    ports:
      - "6379:6379"
    networks:
      - photo-restore-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:7
    container_name: photo-restore-mongo
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGO_DB}
    volumes:
      - ./volumes/mongodb:/data/db
    ports:
      - "27017:27017"
    networks:
      - photo-restore-network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: photo-restore-backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@mariadb:3306/${DB_NAME}
      - MONGODB_URL=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/${MONGO_DB}
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=development
    volumes:
      - ./backend:/app
      - ./volumes/uploads:/app/uploads
      - ./volumes/processed:/app/processed
    ports:
      - "8000:8000"
    depends_on:
      mariadb:
        condition: service_healthy
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy
    networks:
      - photo-restore-network

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: photo-restore-celery
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@mariadb:3306/${DB_NAME}
      - MONGODB_URL=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/${MONGO_DB}
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=development
    volumes:
      - ./backend:/app
      - ./volumes/uploads:/app/uploads
      - ./volumes/processed:/app/processed
    depends_on:
      - backend
      - redis
    networks:
      - photo-restore-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: photo-restore-frontend
    command: npm run dev
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    ports:
      - "5173:5173"
    depends_on:
      - backend
    networks:
      - photo-restore-network

  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: photo-restore-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./volumes/certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    networks:
      - photo-restore-network

networks:
  photo-restore-network:
    driver: bridge

volumes:
  mariadb:
  redis:
  mongodb:
  uploads:
  processed:
  certs:
```

---

## 📋 Variables de Entorno (.env)

```
# Base de Datos
DB_NAME=photo_restore
DB_USER=photo_restore_user
DB_PASSWORD=secure_password_123
DB_ROOT_PASSWORD=root_secure_123
DB_HOST=mariadb
DB_PORT=3306

# MongoDB
MONGO_USER=photo_restore_user
MONGO_PASSWORD=mongo_secure_123
MONGO_DB=photo_restore_jobs
MONGO_HOST=mongodb
MONGO_PORT=27017

# Redis
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=

# JWT
JWT_SECRET_KEY=your_super_secret_key_change_in_production_32_chars_min
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# Backend
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
DEBUG=True
WORKERS=4

# ComfyUI Default (usuario puede sobrescribir)
COMFYUI_DEFAULT_URL=http://localhost:8188
COMFYUI_API_KEY=

# LLM APIs (usuario puede agregar sus propias keys)
OPENAI_API_KEY=sk_test_xxx
ANTHROPIC_API_KEY=sk_test_xxx

# Storage
MAX_FILE_SIZE_MB=50
UPLOAD_FOLDER=/app/uploads
PROCESSED_FOLDER=/app/processed
ALLOWED_EXTENSIONS=jpg,jpeg,png,bmp,tiff

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Seguridad
ENCRYPTION_KEY=your_32_character_encryption_key_
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

---

## 🎯 Flujo Principal de Restauración

### 1. Usuario Sube Foto
```
Frontend → POST /api/v1/uploads (multipart) 
→ Backend valida formato/tamaño 
→ Guarda en ./volumes/uploads 
→ Crea registro en DB (status: 'uploaded')
→ Retorna upload_id
```

### 2. Usuario Configura Parámetros
```
Frontend: Selecciona
- Tipo de restauración: manchas, enfoque, contraste, upscale
- API a usar: OpenAI, Anthropic, Grok
- ComfyUI server (local o remoto)
```

### 3. Backend Procesa con ComfyUI
```
Backend recibe request → POST /api/v1/jobs
→ Valida que user tenga API key configurada
→ Valida ComfyUI server accesible
→ Genera prompt para LLM (OpenAI/Anthropic/Grok)
  usando descripción técnica de restauración
→ LLM retorna workflow JSON para ComfyUI
→ Envia workflow a ComfyUI API
→ ComfyUI procesa imagen (puede ser local o Runpod)
→ Backend descarga resultado
→ Guarda en ./volumes/processed
→ Actualiza job status → 'completed'
→ Retorna URL descargable
```

### 4. Usuario Descarga Resultado
```
Frontend → GET /api/v1/jobs/{id}/result
→ Backend verifica permisos
→ Retorna imagen en alta resolución
```

---

## 🔄 Integración ComfyUI

### Flujo de Workflow
```python
# Backend genera request como:
{
    "image_path": "/uploads/user_123/photo.jpg",
    "restoration_params": {
        "remove_dust": True,
        "enhance_contrast": True,
        "improve_focus": True,
        "upscale_factor": 2,
        "preserve_faces": True
    }
}

# LLM (OpenAI/Anthropic) convierte esto en:
{
    "prompt": "Restore old photo: remove dust, enhance contrast, improve focus, upscale 2x, preserve faces",
    "workflow": {
        # ComfyUI nodes JSON:
        "1": {"class_type": "LoadImage", "inputs": {"image": "photo.jpg"}},
        "2": {"class_type": "RemoveDust", "inputs": {"image": [1, 0]}},
        "3": {"class_type": "ContrastEnhance", "inputs": {"image": [2, 0]}},
        # ... más nodes
    }
}

# Backend envía a ComfyUI
POST http://comfyui:8188/api/prompt
Body: workflow_json

# Recibe job_id y polling
GET http://comfyui:8188/api/history/{job_id}
```

### Templates ComfyUI Disponibles
- **DustRemoval:** Dust & Scratch remover
- **ColorCorrection:** Auto color balance, contrast enhancement
- **Deblur:** Focus improvement
- **Upscaling:** 2x, 4x upscale sin cambiar rostros
- **Denoise:** Noise reduction
- **Combined:** Pipeline completa

---

## 🚀 Iniciar Proyecto

### Prerrequisitos
```bash
- Docker 20.10+
- Docker Compose 2.0+
- ComfyUI instalado localmente O Runpod account
- OpenAI/Anthropic API key
```

### Setup Inicial
```bash
# 1. Clonar repo
git clone <repo>
cd photo-restore-project

# 2. Crear .env
cp .env.example .env
# Editar .env con tus valores

# 3. Build images
docker-compose build

# 4. Iniciar servicios
docker-compose up -d

# 5. Verificar health
docker-compose ps

# 6. Logs
docker-compose logs -f backend
```

### URLs Locales
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MariaDB: localhost:3306
- Redis: localhost:6379
- MongoDB: localhost:27017

---

## 📱 Features Detallados

### Para Usuarios
- ✅ Autenticación segura (JWT)
- ✅ Subir múltiples fotos
- ✅ Preview antes/después
- ✅ Configurar API keys personales
- ✅ Configurar ComfyUI server (local/remoto)
- ✅ Historial de procesamiento
- ✅ Descargar en alta resolución
- ✅ Dashboard con estadísticas
- ✅ Sistema de créditos/cuotas
- ✅ Soporte multi-idioma (i18n)

### Para Backend
- ✅ JWT + Session management
- ✅ Rate limiting
- ✅ Encriptación API keys
- ✅ Procesamiento async con Celery
- ✅ Logging completo
- ✅ Error handling robusto
- ✅ Validación de inputs
- ✅ WebSocket para updates en tiempo real
- ✅ Caché con Redis
- ✅ Histórico en MongoDB

### Para DevOps
- ✅ Docker Compose single command
- ✅ Health checks en todos los servicios
- ✅ Volúmenes persistentes
- ✅ Fácil escalabilidad
- ✅ Reverse proxy Nginx
- ✅ HTTPS ready
- ✅ Environment-based config

---

## 🔧 Configuraciones Especiales

### ComfyUI Remoto (Runpod)
```
1. Usuario compra nodo Runpod con ComfyUI preinstalado
2. En Settings → ComfyUI, ingresa:
   - Server URL: https://your-runpod-id.runpod.io
   - API Key: (si requiere auth)
3. Backend testa conexión antes de procesar
4. Workflows se envían igual que a local
```

### Multi-LLM Setup
```
Usuario puede tener múltiples API keys:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Grok (X.AI)
- Custom (Ollama local, etc)

En settings selecciona cual usar por defecto.
Backend auto-intenta fallback si API falla.
```

---

## 📊 Monitoreo

### Logs
```bash
# Backend logs
docker-compose logs -f backend

# Celery worker logs
docker-compose logs -f celery-worker

# Nginx logs
docker-compose logs -f nginx
```

### Health Checks
```bash
# Verificar servicios
curl http://localhost:8000/health
curl http://localhost:5173

# BD Health
docker-compose exec mariadb mysqladmin ping -h localhost
docker-compose exec redis redis-cli ping
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 📝 Testing

```bash
# Backend tests
docker-compose exec backend pytest tests/ -v

# Frontend tests
docker-compose exec frontend npm test

# E2E tests
npm run cypress:run
```

---

## 🚀 Deploy a Producción

### Cambios necesarios:
1. Cambiar `ENVIRONMENT=production`
2. Generar JWT_SECRET_KEY segura (32+ chars)
3. Certificados SSL reales (Let's Encrypt)
4. CORS_ORIGINS a dominio real
5. Escalar Celery workers si necesario
6. Setup backup automático de BDs
7. Monitoreo con Prometheus/Grafana
8. Rate limiting más estricto

---

## 🛠️ Próximos Pasos Recomendados

1. **Primero:** Estructura base FastAPI + React
2. **Auth:** JWT, login, registro, protección rutas
3. **Upload:** Validación, storage, preview
4. **ComfyUI:** Integración básica con workflows simples
5. **LLM:** OpenAI integration para generar workflows
6. **UI:** Dashboard, configuración user, historial
7. **Refinamiento:** Tests, error handling, optimizaciones
8. **Deploy:** Docker compose completo, CI/CD

---

## 📞 Notas de Desarrollo

- Usar TypeScript estricto en frontend (non-null assertions mínimas)
- Backend con type hints completos (mypy strict mode)
- Logging estructurado (JSON logs en producción)
- Separación clara: models, schemas, services
- No mezclar lógica de BD con lógica de API
- WebSockets para actualizaciones en tiempo real de jobs
- Considerar agregar Stripe para pagos si es necesario
- Documentar workflows ComfyUI usados
- Crear templates de restauración estándar

---

**Última actualización:** Julio 2026
**Versión:** 1.0-alpha
**Estado:** Ready for Claude Code development
