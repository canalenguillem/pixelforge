# Photo Restore Pro - Guía Técnica de Implementación

## 🎯 Ejemplos de Código

### Backend: Core Models (SQLAlchemy)

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("UserAPIKey", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("UserSubscription", back_populates="user", uselist=False)
    comfyui_configs = relationship("ComfyUIConfig", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_email', 'email'),
    )

# app/models/upload.py
class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    width = Column(Integer)
    height = Column(Integer)
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="uploads")
    jobs = relationship("ProcessingJob", back_populates="upload", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_status', 'status'),
    )

# app/models/job.py
class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    status = Column(String(50), default="queued")  # queued, processing, completed, failed
    job_type = Column(String(100))  # restoration, enhancement, upscale
    processed_image_path = Column(String(1000))
    error_message = Column(String(1000))
    processing_time_seconds = Column(Integer)
    comfyui_job_id = Column(String(500))  # ID del job en ComfyUI
    llm_used = Column(String(50))  # openai, anthropic, grok
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    user = relationship("User", back_populates="jobs")
    upload = relationship("Upload", back_populates="jobs")
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )
```

### Backend: Schemas Pydantic

```python
# app/schemas/upload.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UploadBase(BaseModel):
    original_filename: str
    mime_type: str

class UploadCreate(BaseModel):
    pass  # Los datos vienen en multipart/form-data

class UploadResponse(UploadBase):
    id: int
    user_id: int
    storage_path: str
    file_size: int
    width: int
    height: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UploadListResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    status: str
    width: int
    height: int
    created_at: datetime

# app/schemas/job.py
class JobCreate(BaseModel):
    upload_id: int
    job_type: str = "restoration"  # restoration, enhancement, upscale
    llm_provider: Optional[str] = None  # openai, anthropic, grok - usa default del user si no

class JobResponse(BaseModel):
    id: int
    upload_id: int
    status: str
    job_type: str
    processing_time_seconds: Optional[int]
    error_message: Optional[str]
    llm_used: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class JobDetailResponse(JobResponse):
    processed_image_path: Optional[str]
    tokens_used: Optional[int]
```

### Backend: Service Pattern

```python
# app/services/upload_service.py
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.upload import Upload
from app.utils.file_handlers import save_upload_file, get_image_dimensions
from app.utils.exceptions import InvalidFileError
import os

class UploadService:
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validar archivo antes de guardar"""
        ext = file.filename.split('.')[-1].lower()
        if ext not in UploadService.ALLOWED_EXTENSIONS:
            raise InvalidFileError(f"Extensión no permitida: {ext}")
        
        if file.size and file.size > UploadService.MAX_FILE_SIZE:
            raise InvalidFileError(f"Archivo demasiado grande: {file.size} bytes")
    
    @staticmethod
    async def create_upload(
        file: UploadFile,
        user_id: int,
        db: Session,
        upload_folder: str
    ) -> Upload:
        """Crear y guardar upload"""
        # Validar
        UploadService.validate_file(file)
        
        # Guardar archivo
        file_path = await save_upload_file(file, user_id, upload_folder)
        
        # Obtener dimensiones
        width, height = get_image_dimensions(file_path)
        
        # Crear registro en DB
        upload = Upload(
            user_id=user_id,
            original_filename=file.filename,
            storage_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            width=width,
            height=height,
            status="uploaded"
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        return upload
    
    @staticmethod
    def get_user_uploads(
        user_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> list[Upload]:
        """Obtener uploads del usuario paginado"""
        return db.query(Upload)\
            .filter(Upload.user_id == user_id)\
            .order_by(Upload.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def delete_upload(upload_id: int, user_id: int, db: Session) -> None:
        """Eliminar upload y archivo físico"""
        upload = db.query(Upload)\
            .filter(Upload.id == upload_id, Upload.user_id == user_id)\
            .first()
        
        if not upload:
            raise ValueError("Upload no encontrado")
        
        # Eliminar archivo físico
        if os.path.exists(upload.storage_path):
            os.remove(upload.storage_path)
        
        # Eliminar registro
        db.delete(upload)
        db.commit()
```

### Backend: ComfyUI Service

```python
# app/services/comfyui_service.py
import aiohttp
import json
import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings
from app.utils.exceptions import ComfyUIError
import logging

logger = logging.getLogger(__name__)

class ComfyUIService:
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    async def test_connection(self) -> bool:
        """Probar conexión a servidor ComfyUI"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/system_stats",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"ComfyUI connection failed: {e}")
            return False
    
    async def submit_workflow(
        self,
        workflow: Dict[str, Any],
        image_path: str
    ) -> str:
        """Enviar workflow a ComfyUI y retornar job_id"""
        try:
            # Agregar ruta de imagen al workflow
            workflow['image_path'] = image_path
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/api/prompt",
                    json=workflow,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ComfyUIError(f"ComfyUI error: {error_text}")
                    
                    data = await response.json()
                    return data.get('prompt_id')
        except Exception as e:
            logger.error(f"Failed to submit workflow: {e}")
            raise ComfyUIError(str(e))
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtener estado de un job"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/api/history/{job_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 404:
                        return {'status': 'not_found'}
                    
                    data = await response.json()
                    return data.get(job_id, {})
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            raise ComfyUIError(str(e))
    
    async def get_job_result(self, job_id: str) -> Optional[str]:
        """Obtener resultado del job (ruta imagen)"""
        status = await self.get_job_status(job_id)
        
        if 'outputs' in status:
            outputs = status['outputs']
            # Buscar output de imagen
            for key, value in outputs.items():
                if isinstance(value, dict) and 'images' in value:
                    return value['images'][0]['filename']
        
        return None
    
    async def download_result(self, filename: str, save_path: str) -> bool:
        """Descargar imagen resultado"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/view?filename={filename}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        with open(save_path, 'wb') as f:
                            f.write(await response.read())
                        return True
            return False
        except Exception as e:
            logger.error(f"Failed to download result: {e}")
            raise ComfyUIError(str(e))
```

### Backend: LLM Workflow Generator

```python
# app/services/llm_service.py
from typing import Optional, Dict, Any
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMWorkflowGenerator:
    """Genera workflows ComfyUI usando LLM"""
    
    # Templates de prompts
    RESTORATION_PROMPT = """
    You are an expert in photo restoration workflows for ComfyUI.
    
    Image restoration request:
    - Input: {image_path}
    - Restoration type: {job_type}
    - Target: {target_description}
    
    Generate a valid ComfyUI workflow JSON that:
    1. Removes dust, scratches and artifacts
    2. Enhances contrast without oversaturation
    3. Improves focus/sharpness subtly
    4. Upscales by {upscale_factor}x while preserving faces
    5. Maintains original composition and colors
    
    Return ONLY valid JSON in this format:
    {
        "nodes": [
            {{"id": 1, "class_type": "LoadImage", "inputs": {{"image": "image_path"}}}},
            ...
        ]
    }
    """
    
    @staticmethod
    async def generate_workflow_with_openai(
        image_path: str,
        job_type: str,
        api_key: str,
        upscale_factor: int = 2
    ) -> Dict[str, Any]:
        """Generar workflow usando OpenAI"""
        try:
            import openai
            openai.api_key = api_key
            
            target_description = LLMWorkflowGenerator._get_target_description(job_type)
            
            prompt = LLMWorkflowGenerator.RESTORATION_PROMPT.format(
                image_path=image_path,
                job_type=job_type,
                target_description=target_description,
                upscale_factor=upscale_factor
            )
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": "You are a ComfyUI workflow expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            workflow_text = response.choices[0].message.content
            workflow = json.loads(workflow_text)
            
            return workflow
        except Exception as e:
            logger.error(f"OpenAI workflow generation failed: {e}")
            raise
    
    @staticmethod
    async def generate_workflow_with_anthropic(
        image_path: str,
        job_type: str,
        api_key: str,
        upscale_factor: int = 2
    ) -> Dict[str, Any]:
        """Generar workflow usando Anthropic Claude"""
        try:
            from anthropic import AsyncAnthropic
            
            client = AsyncAnthropic(api_key=api_key)
            target_description = LLMWorkflowGenerator._get_target_description(job_type)
            
            prompt = LLMWorkflowGenerator.RESTORATION_PROMPT.format(
                image_path=image_path,
                job_type=job_type,
                target_description=target_description,
                upscale_factor=upscale_factor
            )
            
            message = await client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            workflow_text = message.content[0].text
            workflow = json.loads(workflow_text)
            
            return workflow
        except Exception as e:
            logger.error(f"Anthropic workflow generation failed: {e}")
            raise
    
    @staticmethod
    def _get_target_description(job_type: str) -> str:
        """Descripciones de restauración por tipo"""
        descriptions = {
            "restoration": "Full restoration: dust removal, contrast enhancement, focus improvement",
            "enhancement": "Enhancement only: improve contrast, brightness, clarity",
            "upscale": "Upscale to 4x with quality preservation",
            "denoise": "Remove noise and grain while preserving details"
        }
        return descriptions.get(job_type, descriptions["restoration"])
```

### Backend: Job Service & Celery

```python
# app/services/job_service.py
from sqlalchemy.orm import Session
from app.models.job import ProcessingJob
from app.models.upload import Upload
from app.db.mongo_client import mongodb
from datetime import datetime
import json

class JobService:
    @staticmethod
    def create_job(
        user_id: int,
        upload_id: int,
        job_type: str,
        db: Session
    ) -> ProcessingJob:
        """Crear nuevo job de procesamiento"""
        job = ProcessingJob(
            user_id=user_id,
            upload_id=upload_id,
            job_type=job_type,
            status="queued"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def update_job_status(
        job_id: int,
        status: str,
        db: Session,
        error_message: str = None,
        comfyui_job_id: str = None
    ) -> ProcessingJob:
        """Actualizar estado del job"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = status
        job.error_message = error_message
        if comfyui_job_id:
            job.comfyui_job_id = comfyui_job_id
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    async def log_to_mongodb(
        job_id: int,
        user_id: int,
        upload_id: int,
        comfyui_workflow: dict,
        comfyui_response: dict,
        llm_metadata: dict
    ) -> None:
        """Guardar histórico en MongoDB"""
        history_doc = {
            "job_id": job_id,
            "user_id": user_id,
            "upload_id": upload_id,
            "comfyui_workflow": comfyui_workflow,
            "comfyui_response": comfyui_response,
            "llm_metadata": llm_metadata,
            "created_at": datetime.utcnow(),
            "status": "completed"
        }
        
        collection = mongodb.db["jobs_history"]
        result = await collection.insert_one(history_doc)
        return result.inserted_id

# app/workers/tasks.py
from celery import shared_task
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.comfyui_service import ComfyUIService
from app.services.llm_service import LLMWorkflowGenerator
from app.services.job_service import JobService
from app.models.user import User
from app.models.upload import Upload
import asyncio
import time

@shared_task(name="process_image_restoration")
def process_image_restoration(job_id: int, upload_id: int, user_id: int, llm_provider: str):
    """Tarea Celery para procesar restauración de imagen"""
    db = SessionLocal()
    
    try:
        # Obtener datos
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        # Actualizar estado
        JobService.update_job_status(job_id, "processing", db)
        
        # 1. Obtener API key del usuario para ComfyUI
        comfyui_config = user.comfyui_configs[0]  # Simplificado
        comfyui = ComfyUIService(comfyui_config.server_url, comfyui_config.api_key)
        
        # Verificar conexión
        if not asyncio.run(comfyui.test_connection()):
            raise Exception("ComfyUI server not reachable")
        
        # 2. Obtener API key del LLM
        llm_key = None
        for key in user.api_keys:
            if key.provider == llm_provider:
                llm_key = key.encrypted_key  # Necesita desencriptar
                break
        
        if not llm_key:
            raise Exception(f"No API key for {llm_provider}")
        
        # 3. Generar workflow con LLM
        if llm_provider == "openai":
            workflow = asyncio.run(
                LLMWorkflowGenerator.generate_workflow_with_openai(
                    upload.storage_path,
                    job.job_type,
                    llm_key
                )
            )
        elif llm_provider == "anthropic":
            workflow = asyncio.run(
                LLMWorkflowGenerator.generate_workflow_with_anthropic(
                    upload.storage_path,
                    job.job_type,
                    llm_key
                )
            )
        else:
            raise Exception(f"Unsupported LLM: {llm_provider}")
        
        # 4. Enviar a ComfyUI
        comfyui_job_id = asyncio.run(
            comfyui.submit_workflow(workflow, upload.storage_path)
        )
        JobService.update_job_status(
            job_id,
            "processing",
            db,
            comfyui_job_id=comfyui_job_id
        )
        
        # 5. Poll para resultado
        max_wait = 300  # 5 minutos
        start_time = time.time()
        result_filename = None
        
        while time.time() - start_time < max_wait:
            status = asyncio.run(comfyui.get_job_status(comfyui_job_id))
            
            if 'outputs' in status:
                result_filename = asyncio.run(
                    comfyui.get_job_result(comfyui_job_id)
                )
                break
            
            time.sleep(5)
        
        if not result_filename:
            raise Exception("Processing timeout")
        
        # 6. Descargar resultado
        processed_path = f"/app/processed/{user_id}_{job_id}.png"
        asyncio.run(
            comfyui.download_result(result_filename, processed_path)
        )
        
        # 7. Actualizar job como completado
        processing_time = int(time.time() - start_time)
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = "completed"
        job.processed_image_path = processed_path
        job.processing_time_seconds = processing_time
        job.updated_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # 8. Log a MongoDB
        asyncio.run(JobService.log_to_mongodb(
            job_id, user_id, upload_id,
            workflow, status, {"llm": llm_provider}
        ))
        
    except Exception as e:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        job.updated_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()
```

### Frontend: Upload Hook (React)

```typescript
// frontend/src/hooks/useUpload.ts
import { useState } from 'react';
import { uploadService } from '@/services/upload.service';
import { useAuthStore } from '@/store/authStore';
import { Upload, ProcessingJob } from '@/types';

export function useUpload() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthStore();

  const uploadFile = async (file: File): Promise<Upload> => {
    setIsLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await uploadService.uploadImage(formData);
      setUploads([response, ...uploads]);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUploads = async (page = 1, limit = 20) => {
    setIsLoading(true);
    try {
      const response = await uploadService.getUploads(page, limit);
      setUploads(response.items);
    } catch (err) {
      setError('Failed to fetch uploads');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteUpload = async (uploadId: number) => {
    try {
      await uploadService.deleteUpload(uploadId);
      setUploads(uploads.filter(u => u.id !== uploadId));
    } catch (err) {
      setError('Failed to delete upload');
    }
  };

  return {
    uploads,
    isLoading,
    error,
    uploadFile,
    fetchUploads,
    deleteUpload
  };
}
```

### Frontend: API Service

```typescript
// frontend/src/services/api.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuthStore } from '@/store/authStore';

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const { token } = useAuthStore.getState();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Si token expiró, intentar refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const { refreshToken } = useAuthStore.getState();
        const response = await axios.post(
          `${api.defaults.baseURL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );
        const newToken = response.data.access_token;
        useAuthStore.setState({ token: newToken });
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        useAuthStore.setState({ user: null, token: null });
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### Frontend: Processing Component

```tsx
// frontend/src/components/Editor/ProcessingOptions.tsx
import { useState } from 'react';
import { Card, Button, Select, Checkbox, Slider } from '@/components/ui';
import { jobService } from '@/services/job.service';
import { Upload, ProcessingJob } from '@/types';

interface ProcessingOptionsProps {
  upload: Upload;
  onProcessingStart: (job: ProcessingJob) => void;
  onError: (error: string) => void;
}

export function ProcessingOptions({
  upload,
  onProcessingStart,
  onError
}: ProcessingOptionsProps) {
  const [jobType, setJobType] = useState<'restoration' | 'enhancement' | 'upscale'>('restoration');
  const [llmProvider, setLlmProvider] = useState('openai');
  const [upscaleFactor, setUpscaleFactor] = useState(2);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleStartProcessing = async () => {
    try {
      setIsProcessing(true);
      const job = await jobService.createJob({
        upload_id: upload.id,
        job_type: jobType,
        llm_provider: llmProvider,
        upscale_factor: upscaleFactor
      });
      onProcessingStart(job);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Processing failed';
      onError(message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className="p-6 space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">
          Tipo de Restauración
        </label>
        <Select
          value={jobType}
          onChange={(e) => setJobType(e.target.value as any)}
        >
          <option value="restoration">Restauración Completa</option>
          <option value="enhancement">Mejora de Contraste</option>
          <option value="upscale">Aumento de Resolución</option>
        </Select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">
          Modelo de IA
        </label>
        <Select
          value={llmProvider}
          onChange={(e) => setLlmProvider(e.target.value)}
        >
          <option value="openai">OpenAI (GPT-4)</option>
          <option value="anthropic">Anthropic (Claude 3)</option>
          <option value="grok">Grok (X.AI)</option>
        </Select>
      </div>

      {jobType === 'upscale' && (
        <div>
          <label className="block text-sm font-medium mb-2">
            Factor de Aumento: {upscaleFactor}x
          </label>
          <Slider
            min={2}
            max={4}
            step={1}
            value={upscaleFactor}
            onChange={setUpscaleFactor}
          />
        </div>
      )}

      <Button
        onClick={handleStartProcessing}
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? 'Procesando...' : 'Iniciar Restauración'}
      </Button>
    </Card>
  );
}
```

### Frontend: WebSocket Monitoring

```typescript
// frontend/src/services/websocket.service.ts
class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  connect(jobId: number, token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
      this.ws = new WebSocket(
        `${wsUrl}/api/v1/jobs/${jobId}/stream?token=${token}`
      );

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        this.attemptReconnect(jobId, token);
      };
    });
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.ws) return;

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === event) {
          callback(message.data);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }

  private attemptReconnect(jobId: number, token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect(jobId, token);
      }, this.reconnectDelay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default new WebSocketService();
```

---

## 🔐 Encriptación de API Keys

```python
# app/utils/encryption.py
from cryptography.fernet import Fernet
from app.core.config import settings

class EncryptionService:
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt(self, value: str) -> str:
        """Encriptar string"""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Desencriptar string"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()

# Uso en modelo
class UserAPIKey(Base):
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String(50))
    _encrypted_key = Column('encrypted_key', String(500))
    
    @property
    def encrypted_key(self) -> str:
        return self._encrypted_key
    
    @encrypted_key.setter
    def encrypted_key(self, value: str):
        encryption_service = EncryptionService()
        self._encrypted_key = encryption_service.encrypt(value)
```

---

## 🧪 Testing Examples

```python
# backend/tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal

client = TestClient(app)

def test_register():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_login():
    # Primero registrar
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    
    # Luego login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_upload_image(test_user_token):
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/api/v1/uploads",
            files={"file": ("test.jpg", f, "image/jpeg")},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"
```

---

## 🚀 Deployment Checklist

```
- [ ] Cambiar ENVIRONMENT a 'production'
- [ ] Generar JWT_SECRET_KEY segura (secrets.token_urlsafe(32))
- [ ] Generar ENCRYPTION_KEY para API keys
- [ ] Configurar dominio real en CORS_ORIGINS
- [ ] Obtener certificado SSL (Let's Encrypt)
- [ ] Configurar BD backups automáticos
- [ ] Setup Prometheus/Grafana para monitoreo
- [ ] Configurar logging centralizado (ELK stack)
- [ ] Escalar workers Celery según load
- [ ] Rate limiting más estricto en producción
- [ ] Setup CI/CD (GitHub Actions, GitLab CI)
- [ ] Documentación de API actualizada
- [ ] Tests de integración pasando al 100%
```

---

**Versión:** 1.0
**Listo para:** Claude Code en VS Code
