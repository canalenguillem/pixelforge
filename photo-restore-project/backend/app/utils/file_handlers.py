"""Helpers de almacenamiento de ficheros en disco (uploads).

Los ficheros se guardan bajo UPLOAD_FOLDER/user_{id}/ con un nombre único
(uuid) para evitar colisiones y no exponer el nombre original en el path.
"""

import os
import uuid

from app.core.config import settings


def _user_dir(base: str, user_id: int) -> str:
    directory = os.path.join(base, f"user_{user_id}")
    os.makedirs(directory, exist_ok=True)
    return directory


def save_bytes(user_id: int, extension: str, content: bytes) -> str:
    """Guarda un upload nuevo (UPLOAD_FOLDER) y devuelve su ruta absoluta."""
    filename = f"{uuid.uuid4().hex}.{extension}"
    path = os.path.join(_user_dir(settings.UPLOAD_FOLDER, user_id), filename)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


def save_processed(user_id: int, extension: str, content: bytes) -> str:
    """Guarda un resultado procesado (PROCESSED_FOLDER) y devuelve su ruta."""
    filename = f"{uuid.uuid4().hex}.{extension}"
    path = os.path.join(_user_dir(settings.PROCESSED_FOLDER, user_id), filename)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


def read_file(path: str) -> bytes:
    """Lee el contenido binario de un fichero."""
    with open(path, "rb") as fh:
        return fh.read()


def delete_file(path: str) -> None:
    """Elimina un fichero si existe (no falla si ya no está)."""
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
