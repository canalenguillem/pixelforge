"""Endpoints de configuración (API keys de LLMs, config de ComfyUI).

Placeholder inicial — rutas declaradas sin lógica todavía.
"""

from fastapi import APIRouter

router = APIRouter()

# --- API keys ---------------------------------------------------------------
# TODO: POST   /api-keys        - Guardar API key (encriptada)
# TODO: GET    /api-keys        - Listar API keys (masked)
# TODO: DELETE /api-keys/{id}   - Eliminar API key

# --- ComfyUI ----------------------------------------------------------------
# TODO: POST   /comfyui         - Configurar servidor ComfyUI
# TODO: GET    /comfyui         - Obtener config
# TODO: PUT    /comfyui/{id}    - Actualizar config
# TODO: DELETE /comfyui/{id}    - Eliminar config
# TODO: POST   /comfyui/{id}/test - Probar conexión
