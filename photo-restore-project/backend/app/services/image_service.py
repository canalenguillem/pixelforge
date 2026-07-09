"""Servicio de imágenes: validación y lectura de metadatos (Pillow).

El preprocesamiento pesado (OpenCV) se añadirá con la fase de ComfyUI.
"""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.utils.exceptions import AppError


def get_image_dimensions(content: bytes) -> tuple[int, int]:
    """Devuelve (width, height) validando que el contenido es una imagen real.

    Que Pillow reconozca la cabecera actúa como validación de contenido
    (defensa frente a extensiones falsificadas). Lanza AppError si no lo es.
    """
    try:
        with Image.open(BytesIO(content)) as img:
            return img.width, img.height
    except (UnidentifiedImageError, OSError):
        raise AppError("El archivo no es una imagen válida", 400)
