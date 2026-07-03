import io
import logging

from exceptions.handlers import ValidationError

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

_ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}
_EXTENSION_FALLBACK = {"pdf": "pdf", "docx": "docx", "txt": "txt"}


def _kind_from_upload(filename: str, content_type: str | None) -> str:
    kind = _ALLOWED_CONTENT_TYPES.get(content_type or "")
    if kind:
        return kind
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    kind = _EXTENSION_FALLBACK.get(ext)
    if not kind:
        raise ValidationError(
            f"Unsupported file type '{content_type or ext}'. Upload a PDF, DOCX, or TXT resume."
        )
    return kind


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_txt(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def extract_text(filename: str, content_type: str | None, data: bytes) -> str:
    """Validate an uploaded resume file and extract its plain text."""
    if not data:
        raise ValidationError("Uploaded file is empty.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File too large. Max size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.")

    kind = _kind_from_upload(filename, content_type)

    try:
        if kind == "pdf":
            text = _extract_pdf(data)
        elif kind == "docx":
            text = _extract_docx(data)
        else:
            text = _extract_txt(data)
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Resume text extraction failed for {filename}: {e}")
        raise ValidationError("Could not read this file — it may be corrupted or password-protected.") from e

    text = text.strip()
    if not text:
        raise ValidationError("No readable text found in this resume.")
    return text
