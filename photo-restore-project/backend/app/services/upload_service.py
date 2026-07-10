"""Servicio de gestión de uploads: validación, storage y persistencia."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import UploadStatus
from app.models.job import ProcessingJob
from app.models.upload import Upload
from app.services import image_service, pdf_service
from app.utils import file_handlers, validators
from app.utils.exceptions import AppError, NotFoundError


def create_upload(
    db: Session,
    user_id: int,
    filename: str | None,
    mime_type: str | None,
    content: bytes,
) -> Upload:
    """Valida, guarda en disco y registra un upload en BD."""
    size = len(content)
    extension = validators.validate_upload(filename, size)
    width, height = image_service.get_image_dimensions(content)

    storage_path = file_handlers.save_bytes(user_id, extension, content)

    upload = Upload(
        user_id=user_id,
        original_filename=filename or f"upload.{extension}",
        storage_path=storage_path,
        file_size=size,
        mime_type=mime_type,
        width=width,
        height=height,
        status=UploadStatus.UPLOADED.value,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def create_uploads_from_pdf(
    db: Session, user_id: int, pdf_bytes: bytes, stem: str = "pdf"
) -> list[Upload]:
    """Extrae las fotos del PDF y crea un upload por cada una."""
    photos = pdf_service.extract_photos(pdf_bytes)
    uploads: list[Upload] = []
    for i, (data, ext) in enumerate(photos, start=1):
        try:
            up = create_upload(db, user_id, f"{stem}_{i}.{ext}", f"image/{ext}", data)
            uploads.append(up)
        except AppError:
            continue  # saltar imágenes que no pasen la validación
    if not uploads:
        raise AppError("No se pudo extraer ninguna imagen válida del PDF", 422)
    return uploads


def get_upload(db: Session, user_id: int, upload_id: int) -> Upload:
    """Devuelve un upload propio del usuario o lanza NotFoundError.

    Comprobar la propiedad y responder 404 (no 403) evita filtrar la
    existencia de recursos de otros usuarios.
    """
    upload = db.get(Upload, upload_id)
    if upload is None or upload.user_id != user_id:
        raise NotFoundError("Upload no encontrado")
    return upload


def list_uploads(
    db: Session, user_id: int, page: int, page_size: int
) -> tuple[list[Upload], int]:
    """Lista paginada de uploads del usuario (más recientes primero)."""
    total = (
        db.scalar(select(func.count()).select_from(Upload).where(Upload.user_id == user_id))
        or 0
    )
    items = db.scalars(
        select(Upload)
        .where(Upload.user_id == user_id)
        .order_by(Upload.created_at.desc(), Upload.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def rotate_upload(db: Session, user_id: int, upload_id: int, clockwise: bool) -> Upload:
    """Rota el fichero del upload 90° in-place y actualiza sus dimensiones."""
    upload = get_upload(db, user_id, upload_id)
    content = file_handlers.read_file(upload.storage_path)
    rotated, width, height = image_service.rotate_image(content, clockwise)
    with open(upload.storage_path, "wb") as fh:
        fh.write(rotated)
    upload.width = width
    upload.height = height
    db.commit()
    db.refresh(upload)
    return upload


def delete_upload(db: Session, user_id: int, upload_id: int) -> None:
    """Elimina el upload y TODO lo que cuelga de él (jobs + sus ficheros).

    La FK `ON DELETE CASCADE` borra las filas de processing_jobs; aquí borramos
    además los ficheros de resultado en disco para no dejar huérfanos.
    """
    upload = get_upload(db, user_id, upload_id)

    jobs = db.scalars(
        select(ProcessingJob).where(ProcessingJob.upload_id == upload_id)
    ).all()
    for job in jobs:
        if job.processed_image_path:
            file_handlers.delete_file(job.processed_image_path)

    file_handlers.delete_file(upload.storage_path)
    db.delete(upload)  # cascade elimina las filas de jobs
    db.commit()
