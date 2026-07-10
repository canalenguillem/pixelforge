"""Extracción de imágenes embebidas en PDFs (para álbumes de fotos escaneadas).

Recorre las páginas, saca cada imagen embebida (deduplicando por xref), descarta
las pequeñas (iconos/logos) y normaliza colorspaces raros a JPEG RGB.
"""

from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image

from app.utils.exceptions import AppError

MIN_DIM = 200  # px: por debajo se ignora (iconos, adornos)
MAX_IMAGES = 100  # tope de imágenes extraídas por PDF


def extract_photos(content: bytes) -> list[tuple[bytes, str]]:
    """Devuelve [(bytes, extensión)] de las fotos embebidas en el PDF."""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception:
        raise AppError("No se pudo abrir el PDF", 400)

    results: list[tuple[bytes, str]] = []
    seen: set[int] = set()
    try:
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen:
                    continue
                seen.add(xref)
                extracted = _extract_one(doc, xref)
                if extracted is not None:
                    results.append(extracted)
                    if len(results) >= MAX_IMAGES:
                        return results
    finally:
        doc.close()

    if not results:
        raise AppError(
            "El PDF no contiene imágenes extraíbles (¿es texto o vectorial?)", 422
        )
    return results


def _extract_one(doc: "fitz.Document", xref: int) -> tuple[bytes, str] | None:
    try:
        info = doc.extract_image(xref)
    except Exception:
        return None
    raw = info.get("image")
    if not raw:
        return None
    if info.get("width", 0) < MIN_DIM or info.get("height", 0) < MIN_DIM:
        return None

    ext = (info.get("ext") or "png").lower()
    try:
        im = Image.open(BytesIO(raw))
        im.load()
    except Exception:
        # Formato exótico (JPEG2000, CMYK raro…): re-render vía pixmap a JPEG RGB.
        return _via_pixmap(doc, xref)

    # Si ya es un formato/colorspace estándar, conservamos los bytes originales.
    if im.mode == "RGB" and ext in ("jpeg", "jpg", "png"):
        return raw, ("jpg" if ext == "jpeg" else ext)

    if im.mode != "RGB":
        im = im.convert("RGB")
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "jpg"


def _via_pixmap(doc: "fitz.Document", xref: int) -> tuple[bytes, str] | None:
    try:
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:  # CMYK -> RGB
            pix = fitz.Pixmap(fitz.csRGB, pix)
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)  # quitar alfa
        if pix.width < MIN_DIM or pix.height < MIN_DIM:
            return None
        return pix.tobytes("jpg"), "jpg"
    except Exception:
        return None
