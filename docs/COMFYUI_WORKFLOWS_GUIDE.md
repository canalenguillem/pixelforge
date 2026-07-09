# Photo Restore Pro - ComfyUI & Workflows Guide

## 🎨 ComfyUI Overview

ComfyUI es un UI/API alternativa a Stable Diffusion WebUI con mejor soporte para workflows complejos y API robusta. Para restauración de fotos antiguas usaremos:

- **Instalación:** Local (usuario instala en su PC) o RemotePC/Runpod (nodo GPU compartido)
- **Comunicación:** API REST en puerto 8188
- **Workflows:** JSON que define pipeline de procesamiento de imagen
- **Nodes:** Componentes reutilizables (LoadImage, RemoveDust, Upscale, etc.)

---

## 📦 Extensiones ComfyUI Necesarias

Para restauración de fotos, el usuario debe instalar estas extensiones en ComfyUI:

```bash
# En la carpeta ComfyUI/custom_nodes/

# 1. Upscale models
git clone https://github.com/philz5150/ComfyUI-Upscayl.git

# 2. Image restoration
git clone https://github.com/chflame163/ComfyUI_GFPGANofficial.git

# 3. Denoise & enhancement
git clone https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git

# 4. Face preservation
git clone https://github.com/cubiq/ComfyUI_InstantID.git

# 5. Image manipulation
git clone https://github.com/chflame163/ComfyUI_IPAdapter_plus.git

# 6. Quality enhancement
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelper_nodes_Nvidia.git
```

### Modelos Necesarios

```
ComfyUI/models/
├── checkpoints/
│   ├── realesrgan-x4plus.pth          # Upscaling
│   └── realesrgan-x2plus.pth
├── upscale_models/
│   ├── RealESRGAN_x4plus.pth
│   ├── RealESRGAN_x2plus.pth
│   └── RealESRNet_x4plus.pth
├── gfpgan/
│   └── GFPGANv1.3.pth                 # Face restoration
└── controlnet/
    ├── control_canny.pth
    └── control_depth.pth
```

---

## 🔧 Workflow JSON Structure

ComfyUI usa workflows en JSON donde cada nodo tiene:

```json
{
  "node_id": {
    "class_type": "NombreDelNodo",
    "inputs": {
      "param1": value,
      "image": [previous_node_id, output_index]
    }
  }
}
```

### Ejemplo: Restauración Básica

```json
{
  "1": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "/uploads/old_photo.jpg"
    }
  },
  
  "2": {
    "class_type": "RemoveDust",
    "inputs": {
      "image": [1, 0],
      "strength": 0.7
    }
  },
  
  "3": {
    "class_type": "ContrastEnhance",
    "inputs": {
      "image": [2, 0],
      "contrast": 1.2,
      "brightness": 0.05
    }
  },
  
  "4": {
    "class_type": "GFPGANv1.3",
    "inputs": {
      "image": [3, 0],
      "bg_upsampler": "RealESRGAN_x2plus",
      "aligned": true,
      "only_center_face": false,
      "ext": "auto",
      "weight": 0.5
    }
  },
  
  "5": {
    "class_type": "UpscaleImageBySampling",
    "inputs": {
      "image": [4, 0],
      "upscale_method": "lanczos",
      "scale": 2
    }
  },
  
  "6": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "restored",
      "image": [5, 0]
    }
  }
}
```

---

## 🎯 Workflows por Tipo de Restauración

### 1. RESTORATION (Restauración Completa)

```python
def get_restoration_workflow(image_path: str, upscale_factor: int = 2) -> dict:
    """
    Workflow completo: dust removal, face restoration, upscaling
    """
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_path}},
        
        # Remover polvo y arañazos
        "2": {"class_type": "RemoveDust", "inputs": {"image": [1, 0], "strength": 0.8}},
        
        # Mejorar contraste
        "3": {
            "class_type": "ContrastEnhance",
            "inputs": {
                "image": [2, 0],
                "contrast": 1.3,
                "brightness": 0.1,
                "saturation": 1.1
            }
        },
        
        # Reducir ruido
        "4": {
            "class_type": "Denoise",
            "inputs": {
                "image": [3, 0],
                "model": "NAFNet",
                "strength": 0.6
            }
        },
        
        # Restaurar rostros con GFPGAN
        "5": {
            "class_type": "GFPGANv1.3",
            "inputs": {
                "image": [4, 0],
                "bg_upsampler": None,
                "aligned": False,
                "only_center_face": False,
                "weight": 0.7
            }
        },
        
        # Upscaling de calidad
        "6": {
            "class_type": "UpscaleImageBySampling",
            "inputs": {
                "image": [5, 0],
                "upscale_method": "lanczos",
                "scale": upscale_factor
            }
        },
        
        # Nitidez final
        "7": {
            "class_type": "SharpenImage",
            "inputs": {
                "image": [6, 0],
                "sharpen_amount": 1.0
            }
        },
        
        # Guardar
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "restored",
                "image": [7, 0]
            }
        }
    }
```

### 2. ENHANCEMENT (Solo Mejora de Contraste/Colores)

```python
def get_enhancement_workflow(image_path: str) -> dict:
    """Rápido: solo mejora visual sin faces"""
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_path}},
        
        "2": {
            "class_type": "ContrastEnhance",
            "inputs": {
                "image": [1, 0],
                "contrast": 1.4,
                "brightness": 0.15,
                "saturation": 1.2
            }
        },
        
        "3": {
            "class_type": "Denoise",
            "inputs": {"image": [2, 0], "strength": 0.4}
        },
        
        "4": {
            "class_type": "SharpenImage",
            "inputs": {"image": [3, 0], "sharpen_amount": 0.8}
        },
        
        "5": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "enhanced",
                "image": [4, 0]
            }
        }
    }
```

### 3. UPSCALE (Aumento de Resolución)

```python
def get_upscale_workflow(image_path: str, upscale_factor: int = 4) -> dict:
    """Aumento de resolución 4x preservando detalles"""
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_path}},
        
        # Pre-procesamiento
        "2": {
            "class_type": "Denoise",
            "inputs": {"image": [1, 0], "strength": 0.3}
        },
        
        # Upscale progresivo (RealESRGAN es mejor que lanczos)
        "3": {
            "class_type": "UpscaleWithModel",
            "inputs": {
                "image": [2, 0],
                "upscale_model": "RealESRGAN_x4plus"
            }
        },
        
        # Nitidez adaptativa
        "4": {
            "class_type": "UnsharpMask",
            "inputs": {
                "image": [3, 0],
                "sigma": 1.0,
                "strength": 0.5
            }
        },
        
        "5": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "upscaled_4x",
                "image": [4, 0]
            }
        }
    }
```

### 4. DENOISE (Limpieza de Ruido)

```python
def get_denoise_workflow(image_path: str) -> dict:
    """Remoción de ruido/grano manteniendo detalles"""
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_path}},
        
        # Denoise con diferentes modelos
        "2": {
            "class_type": "Denoise",
            "inputs": {
                "image": [1, 0],
                "model": "NAFNet-GoPro",  # Para fotos viejas
                "strength": 0.8
            }
        },
        
        # Preservar bordes
        "3": {
            "class_type": "PreserveEdges",
            "inputs": {
                "image": [1, 0],
                "denoised_image": [2, 0],
                "strength": 0.3
            }
        },
        
        "4": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "denoised",
                "image": [3, 0]
            }
        }
    }
```

---

## 🔄 API ComfyUI

### 1. Submit Workflow (POST)

```bash
curl -X POST http://localhost:8188/api/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "unique_client_id",
    "number": 1,
    "widget_id_list": [...],
    "widget_name": {"1": {...}, "2": {...}}
  }'
```

**Response:**
```json
{
  "prompt_id": "abc123def456",
  "number": 1,
  "node_errors": {}
}
```

### 2. Get Job Status (GET)

```bash
curl http://localhost:8188/api/history/abc123def456
```

**Response:**
```json
{
  "abc123def456": {
    "outputs": {
      "8": {
        "images": [
          {
            "filename": "restored_abc123.png",
            "subfolder": "results",
            "type": "output"
          }
        ]
      }
    },
    "status": {
      "status_str": "success",
      "completed": true,
      "messages": []
    }
  }
}
```

### 3. Download Result (GET)

```bash
curl http://localhost:8188/view?filename=restored_abc123.png \
  -o restored_photo.png
```

---

## 🐳 Docker Setup para ComfyUI (Opcional Local)

Si el usuario quiere ejecutar ComfyUI en Docker localmente:

```dockerfile
# Dockerfile para ComfyUI
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git .

# Requirements
RUN pip install --no-cache-dir -r requirements.txt

# Extensiones necesarias
RUN cd custom_nodes && \
    git clone https://github.com/philz5150/ComfyUI-Upscayl.git && \
    git clone https://github.com/chflame163/ComfyUI_GFPGANofficial.git

EXPOSE 8188

CMD ["python3", "main.py", "--listen", "0.0.0.0"]
```

```yaml
# docker-compose.yml - agregar servicio ComfyUI
comfyui:
  build:
    context: ./comfyui
    dockerfile: Dockerfile
  container_name: photo-restore-comfyui
  volumes:
    - ./volumes/comfyui/models:/app/models
    - ./volumes/comfyui/input:/app/input
    - ./volumes/comfyui/output:/app/output
  ports:
    - "8188:8188"
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  networks:
    - photo-restore-network
```

---

## 💾 Sistema de Caché para Workflows

Para optimizar procesamiento, implementar caché de workflows:

```python
# app/utils/workflow_cache.py
import hashlib
import json
from app.db.redis_client import redis_client

class WorkflowCache:
    CACHE_TTL = 3600  # 1 hora
    
    @staticmethod
    def get_cache_key(job_type: str, upscale_factor: int = 2) -> str:
        """Generar key único para workflow"""
        data = f"{job_type}_{upscale_factor}"
        return f"workflow:{hashlib.md5(data.encode()).hexdigest()}"
    
    @staticmethod
    def get(job_type: str, upscale_factor: int = 2) -> dict | None:
        """Obtener workflow del caché"""
        key = WorkflowCache.get_cache_key(job_type, upscale_factor)
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    @staticmethod
    def set(job_type: str, workflow: dict, upscale_factor: int = 2) -> None:
        """Guardar workflow en caché"""
        key = WorkflowCache.get_cache_key(job_type, upscale_factor)
        redis_client.setex(
            key,
            WorkflowCache.CACHE_TTL,
            json.dumps(workflow)
        )
```

---

## 🧪 Testing Workflows

```python
# backend/tests/test_workflows.py
import pytest
import json
from app.services.comfyui_service import ComfyUIService
from app.workflows import (
    get_restoration_workflow,
    get_enhancement_workflow,
    get_upscale_workflow
)

@pytest.mark.asyncio
async def test_comfyui_connection():
    """Verificar conexión a ComfyUI"""
    service = ComfyUIService("http://localhost:8188")
    is_connected = await service.test_connection()
    assert is_connected, "ComfyUI server not reachable"

@pytest.mark.asyncio
async def test_restoration_workflow():
    """Probar workflow de restauración"""
    workflow = get_restoration_workflow("/test/image.jpg", upscale_factor=2)
    
    # Validar estructura
    assert "1" in workflow  # LoadImage
    assert workflow["1"]["class_type"] == "LoadImage"
    
    # Validar encadenamiento de nodos
    assert workflow["2"]["inputs"]["image"] == [1, 0]

def test_workflow_json_validity():
    """Verificar que workflows sean JSON válidos"""
    workflows = [
        get_restoration_workflow("/test/img.jpg"),
        get_enhancement_workflow("/test/img.jpg"),
        get_upscale_workflow("/test/img.jpg", 4)
    ]
    
    for workflow in workflows:
        assert isinstance(workflow, dict)
        json_str = json.dumps(workflow)
        assert json.loads(json_str) == workflow
```

---

## 🎨 Parámetros Ajustables

Cada usuario puede personalizar estos parámetros:

```python
class RestorationParams(BaseModel):
    # Dust & scratches removal
    dust_removal_strength: float = 0.7  # 0.0-1.0
    
    # Contrast enhancement
    contrast: float = 1.2  # 0.5-2.0
    brightness: float = 0.1  # -0.5-0.5
    saturation: float = 1.1  # 0.5-2.0
    
    # Noise reduction
    denoise_strength: float = 0.6  # 0.0-1.0
    
    # Face restoration
    face_restoration_weight: float = 0.7  # 0.0-1.0
    
    # Upscaling
    upscale_factor: int = 2  # 2, 3, 4
    upscale_method: str = "lanczos"  # lanczos, bicubic, RealESRGAN
    
    # Sharpening
    sharpen_amount: float = 1.0  # 0.0-2.0
```

---

## ⚡ Performance Tips

### Para ComfyUI Local
- GPU mínima: RTX 3060 (12GB VRAM)
- RAM: 16GB recomendado
- Almacenamiento: SSD para modelos
- Tiempo procesamiento: ~10-30s por imagen

### Para ComfyUI Remoto (Runpod)
- GPU: RTX 4090 (24GB VRAM)
- Precio: $0.20-0.50/hora
- Tiempo: ~5-15s por imagen
- Setup: Pre-instalado con modelos

---

## 🔗 Integración Backend-ComfyUI

```python
# app/services/restoration_service.py
class RestorationService:
    def __init__(self, user_comfyui_config):
        self.comfyui = ComfyUIService(
            user_comfyui_config.server_url,
            user_comfyui_config.api_key
        )
    
    async def restore_photo(
        self,
        image_path: str,
        job_type: str,
        params: RestorationParams
    ) -> str:
        """
        Flujo completo: generar workflow → enviar → esperar → descargar
        """
        # 1. Generar workflow según tipo
        if job_type == "restoration":
            workflow = get_restoration_workflow(
                image_path,
                upscale_factor=params.upscale_factor
            )
        elif job_type == "enhancement":
            workflow = get_enhancement_workflow(image_path)
        else:  # upscale
            workflow = get_upscale_workflow(
                image_path,
                params.upscale_factor
            )
        
        # 2. Aplicar parámetros personalizados
        self._apply_custom_params(workflow, params)
        
        # 3. Enviar a ComfyUI
        job_id = await self.comfyui.submit_workflow(workflow, image_path)
        
        # 4. Esperar resultado
        max_attempts = 120  # 10 minutos
        for attempt in range(max_attempts):
            status = await self.comfyui.get_job_status(job_id)
            
            if 'outputs' in status:
                result_filename = await self.comfyui.get_job_result(job_id)
                return result_filename
            
            await asyncio.sleep(5)
        
        raise TimeoutError("ComfyUI processing timeout")
    
    def _apply_custom_params(self, workflow: dict, params: RestorationParams):
        """Modificar workflow con parámetros del usuario"""
        # Ajustar nodo de RemoveDust
        if "2" in workflow:  # RemoveDust node
            workflow["2"]["inputs"]["strength"] = params.dust_removal_strength
        
        # Ajustar nodo de ContrastEnhance
        if "3" in workflow:
            workflow["3"]["inputs"]["contrast"] = params.contrast
            workflow["3"]["inputs"]["brightness"] = params.brightness
```

---

## 📊 Monitoreo de ComfyUI

```bash
# Health check
curl http://localhost:8188/system_stats

# Response
{
  "gfx_device": "RTX 3060",
  "ram_total": 32000,
  "ram_used": 12000,
  "vram_total": 12000,
  "vram_used": 8000,
  "uptime": 3600
}
```

---

**Última actualización:** Julio 2026
**Versión:** 1.0
