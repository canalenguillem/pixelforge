"""Cliente de integración con ComfyUI (API HTTP).

Primitivos del flujo remoto (funciona con ComfyUI en local, LAN o remoto):

    1. check_connection  -> GET  /system_stats
    2. upload_image      -> POST /upload/image   (envía la foto a ComfyUI)
    3. submit_prompt     -> POST /prompt          (encola el workflow)
    4. get_history       -> GET  /history/{id}    (estado/resultado; polling)
    5. download_image    -> GET  /view            (descarga el resultado)

La orquestación (crear job, esperar, guardar resultado) vive en job_service /
el worker de Celery, no aquí.
"""

import asyncio
import json
import time
import uuid
from collections.abc import Callable
from typing import Any

import httpx
import websockets

from app.utils.exceptions import AppError

# Timeouts generosos: subir/descargar imágenes grandes puede tardar.
_CONNECT_TIMEOUT = 10.0
_DEFAULT_TIMEOUT = 60.0


def _client(base_url: str, api_key: str | None = None, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Client:
    headers: dict[str, str] = {}
    if api_key:
        # ComfyUI no trae auth; un reverse proxy delante puede validar este token.
        headers["Authorization"] = f"Bearer {api_key}"
    return httpx.Client(
        base_url=base_url.rstrip("/"),
        headers=headers,
        timeout=httpx.Timeout(timeout, connect=_CONNECT_TIMEOUT),
    )


def _wrap_error(base_url: str, exc: httpx.HTTPError) -> AppError:
    return AppError(f"Error comunicando con ComfyUI ({base_url}): {exc}", 502)


# -----------------------------------------------------------------------------
# 1) Conectividad
# -----------------------------------------------------------------------------
def check_connection(base_url: str, api_key: str | None = None) -> dict[str, Any]:
    """Comprueba que ComfyUI responde y devuelve su system_stats."""
    try:
        with _client(base_url, api_key, timeout=_CONNECT_TIMEOUT) as client:
            resp = client.get("/system_stats")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        raise _wrap_error(base_url, exc)


# -----------------------------------------------------------------------------
# 2) Subir imagen a ComfyUI (a su carpeta input/)
# -----------------------------------------------------------------------------
def upload_image(
    base_url: str,
    filename: str,
    content: bytes,
    api_key: str | None = None,
    subfolder: str = "",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Sube una imagen a ComfyUI. Devuelve {name, subfolder, type}."""
    files = {"image": (filename, content, "application/octet-stream")}
    data: dict[str, str] = {"overwrite": "true" if overwrite else "false"}
    if subfolder:
        data["subfolder"] = subfolder
    try:
        with _client(base_url, api_key) as client:
            resp = client.post("/upload/image", files=files, data=data)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        raise _wrap_error(base_url, exc)


# -----------------------------------------------------------------------------
# 3) Encolar workflow
# -----------------------------------------------------------------------------
def submit_prompt(
    base_url: str,
    workflow: dict[str, Any],
    client_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Encola un workflow (formato API de ComfyUI). Devuelve el prompt_id."""
    payload: dict[str, Any] = {"prompt": workflow}
    if client_id:
        payload["client_id"] = client_id
    try:
        with _client(base_url, api_key) as client:
            resp = client.post("/prompt", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise _wrap_error(base_url, exc)

    node_errors = data.get("node_errors")
    if node_errors:
        raise AppError(f"ComfyUI rechazó el workflow: {node_errors}", 422)
    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise AppError("ComfyUI no devolvió prompt_id", 502)
    return str(prompt_id)


# -----------------------------------------------------------------------------
# 4) Estado / resultado
# -----------------------------------------------------------------------------
def get_history(base_url: str, prompt_id: str, api_key: str | None = None) -> dict[str, Any]:
    """Devuelve la entrada de /history para un prompt_id (vacío si aún no está)."""
    try:
        with _client(base_url, api_key) as client:
            resp = client.get(f"/history/{prompt_id}")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        raise _wrap_error(base_url, exc)


def wait_for_completion(
    base_url: str,
    prompt_id: str,
    api_key: str | None = None,
    timeout: float = 600.0,
    poll_interval: float = 2.0,
) -> list[dict[str, str]]:
    """Hace polling hasta que el prompt termina. Devuelve las imágenes de salida.

    Pensado para ejecutarse en el worker de Celery (usa time.sleep, bloqueante).
    Cada imagen es {filename, subfolder, type}.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        history = get_history(base_url, prompt_id, api_key)
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") == "success":
                return _extract_output_images(entry)
            if status.get("status_str") == "error":
                raise AppError("ComfyUI reportó un error procesando el workflow", 502)
        time.sleep(poll_interval)
    raise AppError(f"Timeout esperando el resultado de ComfyUI ({timeout:.0f}s)", 504)


def _extract_output_images(history_entry: dict[str, Any]) -> list[dict[str, str]]:
    """Extrae las imágenes de salida de una entrada de /history."""
    images: list[dict[str, str]] = []
    for node_output in history_entry.get("outputs", {}).values():
        for image in node_output.get("images", []):
            if image.get("type") == "output":
                images.append(
                    {
                        "filename": image["filename"],
                        "subfolder": image.get("subfolder", ""),
                        "type": image.get("type", "output"),
                    }
                )
    return images


# -----------------------------------------------------------------------------
# 4-bis) Ejecutar con progreso en vivo (WebSocket de ComfyUI)
# -----------------------------------------------------------------------------
def run_with_progress(
    base_url: str,
    workflow: dict[str, Any],
    api_key: str | None = None,
    on_progress: Callable[[int, int, str | None], None] | None = None,
    timeout: float = 600.0,
) -> list[dict[str, str]]:
    """Encola el workflow y escucha el WS de ComfyUI para progreso en vivo.

    Devuelve las imágenes de salida. `on_progress(value, maximum, node)` se
    invoca en cada paso del sampler. Pensado para el worker de Celery.
    """
    return asyncio.run(_run_with_progress(base_url, workflow, api_key, on_progress, timeout))


async def _run_with_progress(
    base_url: str,
    workflow: dict[str, Any],
    api_key: str | None,
    on_progress: Callable[[int, int, str | None], None] | None,
    timeout: float,
) -> list[dict[str, str]]:
    client_id = uuid.uuid4().hex
    ws_url = (
        base_url.rstrip("/").replace("https://", "wss://").replace("http://", "ws://")
        + f"/ws?clientId={client_id}"
    )
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    prompt_id: str | None = None
    try:
        async with websockets.connect(
            ws_url, additional_headers=headers, max_size=None, open_timeout=15
        ) as ws:
            # Encolar el prompt asociándolo a este client_id (para recibir su progreso).
            prompt_id = submit_prompt(base_url, workflow, client_id=client_id, api_key=api_key)

            async with asyncio.timeout(timeout):
                async for message in ws:
                    if isinstance(message, bytes):
                        continue  # imágenes de preview binarias: ignorar
                    data = json.loads(message)
                    mtype = data.get("type")
                    d = data.get("data") or {}
                    if mtype == "progress" and on_progress:
                        if d.get("prompt_id") in (None, prompt_id):
                            on_progress(int(d.get("value", 0)), int(d.get("max", 1)), d.get("node"))
                    elif (
                        mtype == "executing"
                        and d.get("node") is None
                        and d.get("prompt_id") == prompt_id
                    ):
                        break
                    elif mtype == "execution_error" and d.get("prompt_id") == prompt_id:
                        raise AppError(
                            f"ComfyUI error: {d.get('exception_message', 'desconocido')}", 502
                        )
    except (OSError, websockets.WebSocketException) as exc:
        raise AppError(f"Error en el WebSocket de ComfyUI: {exc}", 502)
    except TimeoutError:
        raise AppError(f"Timeout esperando a ComfyUI ({timeout:.0f}s)", 504)

    history = get_history(base_url, prompt_id, api_key)
    return _extract_output_images(history.get(prompt_id, {}))


# -----------------------------------------------------------------------------
# 5) Descargar imagen de salida
# -----------------------------------------------------------------------------
def download_image(
    base_url: str,
    filename: str,
    subfolder: str = "",
    image_type: str = "output",
    api_key: str | None = None,
) -> bytes:
    """Descarga los bytes de una imagen de ComfyUI (endpoint /view)."""
    params = {"filename": filename, "subfolder": subfolder, "type": image_type}
    try:
        with _client(base_url, api_key) as client:
            resp = client.get("/view", params=params)
            resp.raise_for_status()
            return resp.content
    except httpx.HTTPError as exc:
        raise _wrap_error(base_url, exc)
