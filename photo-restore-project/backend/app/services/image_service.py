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


def rotate_image(content: bytes, clockwise: bool) -> tuple[bytes, int, int]:
    """Rota la imagen 90° (clockwise=derecha, else izquierda).

    Devuelve (bytes, width, height) en el mismo formato (JPEG re-encodea a q95).
    """
    try:
        im = Image.open(BytesIO(content))
        im.load()
    except (UnidentifiedImageError, OSError):
        raise AppError("El archivo no es una imagen válida", 400)

    fmt = (im.format or "PNG").upper()
    transpose = Image.Transpose.ROTATE_270 if clockwise else Image.Transpose.ROTATE_90
    rotated = im.transpose(transpose)

    if fmt in ("JPG", "MPO"):
        fmt = "JPEG"
    if fmt == "JPEG" and rotated.mode not in ("RGB", "L"):
        rotated = rotated.convert("RGB")

    buf = BytesIO()
    params = {"quality": 95} if fmt == "JPEG" else {}
    rotated.save(buf, format=fmt, **params)
    return buf.getvalue(), rotated.width, rotated.height
