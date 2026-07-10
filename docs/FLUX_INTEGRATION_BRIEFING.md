# PixelForge — Flux Context Integration Briefing

> Documento de especificación para agregar Flux Context + Qwen-Edit como alternativas de restauración.
> Basado en: video tutorial (Flux Kontext + LLM Toolkit), estado actual del proyecto (handoff 2026-07-10).
> Destino: Claude Code en VS Code para ejecución automatizada.

---

## 1. Overview de la Feature

**Objetivo:** Dar al usuario opciones de workflow de restauración:
- **Epic (actual)**: `epicrealism` + Tile ControlNet + CodeFormer + RealESRGAN (rápido, buena calidad).
- **Flux Context (nuevo)**: Modelo Flux cuantizado (Q8 GGUF) + HDR LoRA (opcional) → calidad superior, más fiel.
- **(Futuro) Qwen-Edit**: alternativa ligera sin LoRA.

**Alcance de este briefing:**
1. Extensión de API: parámetro `workflow_mode` en POST `/jobs`.
2. Nuevos workflows en `workflows.py`: `build_restoration_flux_workflow()`.
3. Frontend: selector radio (Epic / Flux), toggle HDR LoRA.
4. Celery: routing de tareas según modo.
5. Modelos: documentar qué descargar en ComfyUI (192.168.1.46).

**Cambios DB:** Mínimos (tabla `jobs` ya tiene columnas suficientes para metadata adicional).

---

## 2. Cambios en API

### Extender `POST /jobs`

**Actualmente:**
```json
{
  "upload_id": "uuid",
  "restoration_strength": 0.35,
  "codeformer_fidelity": 0.8
}
```

**Nuevo request body:**
```json
{
  "upload_id": "uuid",
  
  "workflow_mode": "epic",  // NEW: "epic" | "flux", default: "epic"
  
  // Parámetros específicos de Epic (ignorados si mode=flux):
  "restoration_strength": 0.35,
  "codeformer_fidelity": 0.8,
  
  // Parámetros específicos de Flux (ignorados si mode=epic):
  "enable_hdr_lora": false,  // NEW: boolean, default: false
  "flux_denoise": 0.4        // NEW: [0.2 fiel ... 0.7 agresivo], default: 0.4
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "workflow_mode": "flux",  // NEW: espejo del request
  "created_at": "2026-07-10T12:30:00Z"
}
```

**GET `/jobs/{id}` response:**
```json
{
  "id": "uuid",
  "upload_id": "uuid",
  "workflow_mode": "epic",
  "status": "completed",
  "metadata": {
    "workflow_mode": "epic",
    "restoration_strength": 0.35,
    "codeformer_fidelity": 0.8,
    "enable_hdr_lora": false,  // NEW
    "flux_denoise": 0.4         // NEW
  },
  "created_at": "...",
  "completed_at": "..."
}
```

### Schema cambios (Pydantic)

**`backend/app/schemas/job.py`:**

```python
from enum import Enum
from typing import Optional

class WorkflowMode(str, Enum):
    EPIC = "epic"
    FLUX = "flux"

class JobCreate(BaseModel):
    upload_id: UUID
    workflow_mode: WorkflowMode = WorkflowMode.EPIC
    restoration_strength: float = 0.35  # solo si mode=EPIC
    codeformer_fidelity: float = 0.8    # solo si mode=EPIC
    enable_hdr_lora: bool = False       # solo si mode=FLUX
    flux_denoise: float = 0.4           # solo si mode=FLUX [0.2..0.7]

    @field_validator("restoration_strength", "flux_denoise")
    @classmethod
    def validate_ranges(cls, v, info):
        if info.field_name == "restoration_strength":
            if not (0.2 <= v <= 0.5):
                raise ValueError("restoration_strength must be [0.2..0.5]")
        elif info.field_name == "flux_denoise":
            if not (0.2 <= v <= 0.7):
                raise ValueError("flux_denoise must be [0.2..0.7]")
        return v

class JobResponse(BaseModel):
    id: UUID
    user_id: UUID
    upload_id: UUID
    workflow_mode: WorkflowMode
    status: str  # queued, processing, completed, failed
    metadata: dict  # {workflow_mode, restoration_strength, ...}
    created_at: datetime
    completed_at: Optional[datetime] = None
```

---

## 3. Workflows en ComfyUI

### 3.1. `build_restoration_flux_workflow()` (Python en `workflows.py`)

```python
def build_restoration_flux_workflow(
    image_path: str,
    enable_hdr_lora: bool = False,
    denoise: float = 0.4
) -> dict:
    """
    Flux Context workflow con LoRA opcional.
    
    Flujo:
      1. Cargar imagen (scale a lado largo 1024)
      2. GGUF Loader: cargar Flux Context Q8 cuantizado
      3. (Opcional) LoRA Loader: HDR LoRA
      4. K Sampler: denoise=denoise (0.2 fiel, 0.7 agresivo)
      5. RealESRGAN x2 (upscale)
      6. Salida
    
    Args:
        image_path: ruta absoluta en ComfyUI server
        enable_hdr_lora: si True, aplica HDR LoRA antes del K Sampler
        denoise: [0.2..0.7], default 0.4 (equilibrio restauración/fidelidad)
    
    Returns:
        dict: workflow JSON listo para `submit_prompt()`
    """
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "flux-dev-Q8.gguf"  # GGUF cuantizado
            }
        },
        "2": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["3", 0],
                "width": 1024,
                "height": 1024,
                "upscale_method": "bicubic"
            }
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_path
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": "restore and enhance old photograph, photo restoration, enhanced details, clear, crisp"
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": "blurry, low quality, artifacts"
            }
        }
    }
    
    # LoRA opcional (si enable_hdr_lora=True)
    if enable_hdr_lora:
        workflow["6"] = {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "HDR-LoRA-flux.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "model": ["1", 0],
                "clip": ["1", 1]
            }
        }
        model_input = ["6", 0]
        clip_input = ["6", 1]
    else:
        model_input = ["1", 0]
        clip_input = ["1", 1]
    
    # K Sampler con denoise controlado
    workflow["7"] = {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 24,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": denoise,
            "model": model_input,
            "positive": ["4", 0],
            "negative": ["5", 0],
            "latent_image": ["8", 0]
        }
    }
    
    # VAE Encode (input)
    workflow["8"] = {
        "class_type": "VAEEncode",
        "inputs": {
            "pixels": ["2", 0],
            "vae": ["1", 2]
        }
    }
    
    # VAE Decode (output)
    workflow["9"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["7", 0],
            "vae": ["1", 2]
        }
    }
    
    # Upscale RealESRGAN x2
    workflow["10"] = {
        "class_type": "LatentUpscale",
        "inputs": {
            "samples": ["7", 0],
            "upscale_method": "nearest-exact",
            "width": 2048,
            "height": 2048
        }
    }
    
    workflow["11"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["10", 0],
            "vae": ["1", 2]
        }
    }
    
    # Upscaler real (si tienes el node instalado)
    workflow["12"] = {
        "class_type": "UpscaleModelLoader",
        "inputs": {
            "upscale_model": "RealESRGAN_x2.pth"
        }
    }
    
    workflow["13"] = {
        "class_type": "ImageUpscaleWithModel",
        "inputs": {
            "upscale_model": ["12", 0],
            "image": ["9", 0]
        }
    }
    
    # SaveImage (output)
    workflow["14"] = {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "flux_restore",
            "images": ["13", 0]
        }
    }
    
    return workflow
```

**Notas:**
- El workflow asume que `flux-dev-Q8.gguf` y `HDR-LoRA-flux.safetensors` están instalados en ComfyUI.
- El `denoise` controla qué tan agresiva es la restauración (0.2 = muy fiel, 0.7 = muy restaurada).
- El prompt es genérico; en v2 se podría hacer dinámico o usar LLM Toolkit.

---

## 4. Cambios en Celery (workers/tasks.py)

### Extender `process_restoration_job()`

**Hoy:**
```python
@celery_app.task(name="process_restoration_job")
def process_restoration_job(job_id: str):
    # Usa build_restoration_workflow() directamente
    ...
```

**Nuevo (routing por workflow_mode):**

```python
@celery_app.task(name="process_restoration_job", bind=True)
def process_restoration_job(self, job_id: str):
    """
    Route según job.metadata['workflow_mode'].
    """
    try:
        job = session.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        workflow_mode = job.metadata.get("workflow_mode", "epic")
        
        # Cargar imagen
        image_path = ...  # path en ComfyUI
        
        if workflow_mode == "epic":
            workflow = build_restoration_workflow(
                image_path=image_path,
                restoration_strength=job.metadata["restoration_strength"],
                codeformer_fidelity=job.metadata["codeformer_fidelity"]
            )
        elif workflow_mode == "flux":
            workflow = build_restoration_flux_workflow(
                image_path=image_path,
                enable_hdr_lora=job.metadata.get("enable_hdr_lora", False),
                denoise=job.metadata.get("flux_denoise", 0.4)
            )
        else:
            raise ValueError(f"Unknown workflow_mode: {workflow_mode}")
        
        # Ejecutar y procesar
        result = comfyui_service.run_with_progress(
            workflow=workflow,
            job_id=job_id,
            progress_callback=lambda p: redis_client.publish(
                f"job:{job_id}:progress",
                json.dumps({"progress": p, "status": "processing"})
            )
        )
        
        # Guardar resultado
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        session.commit()
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job.status = "failed"
        session.commit()
        raise
```

---

## 5. Cambios en Frontend

### 5.1 Schema TypeScript (`src/types/index.ts`)

```typescript
export enum WorkflowMode {
  EPIC = "epic",
  FLUX = "flux"
}

export interface RestoreJobRequest {
  upload_id: string;
  workflow_mode: WorkflowMode;
  
  // Epic params
  restoration_strength?: number;  // [0.2..0.5], default 0.35
  codeformer_fidelity?: number;   // [0..1], default 0.8
  
  // Flux params
  enable_hdr_lora?: boolean;      // default false
  flux_denoise?: number;          // [0.2..0.7], default 0.4
}

export interface RestoreJobResponse {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  workflow_mode: WorkflowMode;
  created_at: string;
}
```

### 5.2 Componente de selector (`src/components/Upload/RestoreOptions.tsx`)

Crear nuevo componente:

```typescript
import React, { useState } from "react";
import { WorkflowMode, RestoreJobRequest } from "../../types";

interface RestoreOptionsProps {
  onStart: (config: RestoreJobRequest) => void;
  loading: boolean;
}

export const RestoreOptions: React.FC<RestoreOptionsProps> = ({
  onStart,
  loading
}) => {
  const [mode, setMode] = useState<WorkflowMode>(WorkflowMode.EPIC);
  const [epicParams, setEpicParams] = useState({
    restoration_strength: 0.35,
    codeformer_fidelity: 0.8
  });
  const [fluxParams, setFluxParams] = useState({
    enable_hdr_lora: false,
    flux_denoise: 0.4
  });

  const handleStart = () => {
    const config: RestoreJobRequest = {
      upload_id: "", // será seteado por el padre
      workflow_mode: mode,
      ...epicParams,
      ...fluxParams
    };
    onStart(config);
  };

  return (
    <div className="space-y-6 p-4 bg-gray-50 rounded-lg">
      {/* Selector de workflow */}
      <div>
        <h3 className="font-semibold mb-3">Restoration Mode</h3>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="radio"
              name="workflow"
              value="epic"
              checked={mode === WorkflowMode.EPIC}
              onChange={() => setMode(WorkflowMode.EPIC)}
              className="mr-3"
            />
            <span>
              <strong>Epic</strong> — Fast & reliable (current)
            </span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="workflow"
              value="flux"
              checked={mode === WorkflowMode.FLUX}
              onChange={() => setMode(WorkflowMode.FLUX)}
              className="mr-3"
            />
            <span>
              <strong>Flux Context</strong> — Superior quality
            </span>
          </label>
        </div>
      </div>

      {/* Parámetros Epic */}
      {mode === WorkflowMode.EPIC && (
        <div className="space-y-4 p-3 bg-white rounded border border-gray-200">
          <div>
            <label className="block text-sm font-medium mb-2">
              Restoration Strength: {epicParams.restoration_strength.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.2"
              max="0.5"
              step="0.05"
              value={epicParams.restoration_strength}
              onChange={(e) =>
                setEpicParams({
                  ...epicParams,
                  restoration_strength: parseFloat(e.target.value)
                })
              }
              className="w-full"
            />
            <small className="text-gray-600">0.2 = faithful, 0.5 = aggressive</small>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              CodeFormer Fidelity: {epicParams.codeformer_fidelity.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={epicParams.codeformer_fidelity}
              onChange={(e) =>
                setEpicParams({
                  ...epicParams,
                  codeformer_fidelity: parseFloat(e.target.value)
                })
              }
              className="w-full"
            />
            <small className="text-gray-600">0 = sharp, 1 = smooth faces</small>
          </div>
        </div>
      )}

      {/* Parámetros Flux */}
      {mode === WorkflowMode.FLUX && (
        <div className="space-y-4 p-3 bg-white rounded border border-gray-200">
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={fluxParams.enable_hdr_lora}
                onChange={(e) =>
                  setFluxParams({
                    ...fluxParams,
                    enable_hdr_lora: e.target.checked
                  })
                }
                className="mr-3"
              />
              <span>Enable HDR LoRA (increased vibrancy)</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Denoise Strength: {fluxParams.flux_denoise.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.2"
              max="0.7"
              step="0.05"
              value={fluxParams.flux_denoise}
              onChange={(e) =>
                setFluxParams({
                  ...fluxParams,
                  flux_denoise: parseFloat(e.target.value)
                })
              }
              className="w-full"
            />
            <small className="text-gray-600">0.2 = faithful, 0.7 = aggressive restoration</small>
          </div>
        </div>
      )}

      {/* Botón */}
      <button
        onClick={handleStart}
        disabled={loading}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Processing..." : "Restore Photo"}
      </button>
    </div>
  );
};
```

### 5.3 Integración en página de Upload

En `src/pages/Upload.tsx`:

```typescript
// (pseudocódigo, adaptar a tu estructura)
const [config, setConfig] = useState<RestoreJobRequest | null>(null);

const handleRestoreOptions = (cfg: RestoreJobRequest) => {
  setConfig({
    ...cfg,
    upload_id: uploadedImageId  // del estado global
  });
  submitRestoreJob(cfg);
};

return (
  <>
    {uploadedImageId && (
      <RestoreOptions onStart={handleRestoreOptions} loading={isProcessing} />
    )}
    {/* ... resultado */}
  </>
);
```

---

## 6. Modelos a descargar en ComfyUI

En la máquina Windows (192.168.1.46):

### 6.1 Descargas requeridas

| Modelo | Fuente | Ruta en ComfyUI | Tamaño | Notas |
|--------|--------|-----------------|--------|-------|
| `flux-dev-Q8.gguf` | Hugging Face / Replicate | `models\diffusion_models\flux\` | ~8 GB | Cuantizado Q8, cabe en VRAM |
| `HDR-LoRA-flux.safetensors` | Link video o HF | `models\loras\` | ~200 MB | Opcional, mejora vibrancia |

### 6.2 Custom Nodes (si no están instalados)

En ComfyUI Manager:
- `Comfy UI GGUF` (para cargar .gguf cuantizados)
- Verificar que `facerestore_cf` siga instalado (para Epic, si lo usas)

### 6.3 Script para descargar (PowerShell, en la máquina Windows)

```powershell
# SSH a la máquina Windows y ejecutar:
$comfyui_path = "D:\AI\ComfyUI"
$models_path = "$comfyui_path\models\diffusion_models\flux"

# Crear carpeta si no existe
New-Item -ItemType Directory -Force -Path $models_path

# Descargar Flux Q8 (ejemplo con huggingface-hub CLI)
# Alternativa: bajar manualmente desde HF y copiar

cd $comfyui_path
# python -m huggingface_hub download <repo_id> flux-dev-Q8.gguf --local-dir models/diffusion_models/flux
```

**Verificación**: En ComfyUI UI, al recargar, debe listar `flux-dev-Q8.gguf` en dropdown de checkpoints.

---

## 7. Database (cambios mínimos)

### Schema `jobs` table (ya existe)

La tabla `jobs` ya tiene una columna `metadata` (JSON o TEXT). Verificar que esté presente:

```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS metadata JSON DEFAULT NULL;
```

**Contenido de `metadata` por workflow:**

Epic:
```json
{
  "workflow_mode": "epic",
  "restoration_strength": 0.35,
  "codeformer_fidelity": 0.8
}
```

Flux:
```json
{
  "workflow_mode": "flux",
  "enable_hdr_lora": false,
  "flux_denoise": 0.4
}
```

**No se necesitan tablas nuevas** — los parámetros se guardan en `metadata` JSONB/JSON.

---

## 8. Testing & Validation

### 8.1 Test manual (cURL)

```bash
# 1. Autenticar
TOKEN=$(curl -s -X POST http://localhost:5273/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@example.com","password":"supersecret123"}' \
  | jq -r '.access_token')

# 2. Subir imagen
UPLOAD_ID=$(curl -s -X POST http://localhost:5273/api/v1/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_photo.jpg" \
  | jq -r '.id')

# 3. Restaurar con Epic
curl -s -X POST http://localhost:5273/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"upload_id\": \"$UPLOAD_ID\",
    \"workflow_mode\": \"epic\",
    \"restoration_strength\": 0.35,
    \"codeformer_fidelity\": 0.8
  }"

# 4. Restaurar con Flux
curl -s -X POST http://localhost:5273/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"upload_id\": \"$UPLOAD_ID\",
    \"workflow_mode\": \"flux\",
    \"enable_hdr_lora\": true,
    \"flux_denoise\": 0.4
  }"

# 5. Monitorear progreso
JOB_ID="<job_id_del_paso_anterior>"
curl -s http://localhost:5273/api/v1/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 8.2 Test del workflow JSON (en ComfyUI directamente)

```bash
# Dentro del contenedor backend:
docker compose exec -T backend python << 'EOF'
from app.services.workflows import build_restoration_flux_workflow
import json

workflow = build_restoration_flux_workflow(
    image_path="/tmp/test.jpg",
    enable_hdr_lora=False,
    denoise=0.4
)

print(json.dumps(workflow, indent=2))
EOF
```

---

## 9. Rollout Plan para Claude Code

**Orden de implementación:**

1. **Schemas** (`backend/app/schemas/job.py`): Agregar `WorkflowMode`, extender `JobCreate`, `JobResponse`.
2. **Workflows** (`backend/app/services/workflows.py`): Implementar `build_restoration_flux_workflow()`.
3. **API endpoints** (`backend/app/api/v1/endpoints/jobs.py`): Actualizar `POST /jobs` para aceptar nuevos parámetros, guardar en metadata.
4. **Celery** (`backend/app/workers/tasks.py`): Routing en `process_restoration_job()` según `workflow_mode`.
5. **Frontend Types** (`src/types/index.ts`): `WorkflowMode`, interfaces.
6. **Frontend Component** (`src/components/Upload/RestoreOptions.tsx`): Nuevo componente con selectores.
7. **Frontend Integration** (`src/pages/Upload.tsx`): Usar `RestoreOptions`.
8. **Testing**: Scripts cURL, verificación de workflow JSON.

**Nota:** No tocar el flujo de inpainting (`build_inpaint_workflow`, `process_inpaint_job`) — se mantiene igual.

---

## 10. Notas y consideraciones

- **ComfyUI:** Verificar que `flux-dev-Q8.gguf` esté instalado en `192.168.1.46:8188` antes de ejecutar jobs con `workflow_mode=flux`. Error handling: si falla la conexión, devolver 503 y msg claro.
- **Latencia:** Flux puede ser más lento que Epic (más pasos de difusión). Considerar parámetro `steps` dinámico si es necesario.
- **Upscaling:** Hoy usa RealESRGAN x2. Flux podría no necesitar upscale adicional si el prompt/denoise es bueno. Tomar decisión después de tests.
- **Future:** LLM Toolkit (generar prompts dinámicos) puede agregarse después como "Advanced Mode".
- **Historial:** Actualizar MongoDB (punto 2 del roadmap anterior) para incluir `workflow_mode` en historial.

---

## 11. Ficheros a crear/modificar

```
✏️  CREAR:
    src/components/Upload/RestoreOptions.tsx

✏️  MODIFICAR:
    backend/app/schemas/job.py
    backend/app/services/workflows.py
    backend/app/api/v1/endpoints/jobs.py
    backend/app/workers/tasks.py
    src/types/index.ts
    src/pages/Upload.tsx
    (opcionalmente) backend/sql/init.sql si quieres migración formal para metadata

✅  NO TOCAR:
    build_inpaint_workflow, process_inpaint_job
    Upload component (subida seguirá igual)
```

---

## Listo para Claude Code

Pasa este fichero a Claude Code en VS Code. Debería tener contexto completo para:
- Generar los esquemas, workflows, endpoints sin paradas.
- Crear el componente React.
- Testear con cURL.

Cualquier pregunta en el briefing: marcar con `[?]` y aclarar antes de ejecutar.