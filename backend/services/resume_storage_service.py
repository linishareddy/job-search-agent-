"""Filesystem storage for uploaded resume originals and generated DOCX artifacts."""
import uuid
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
STORAGE_ROOT = _BACKEND_ROOT / "storage"


def _resume_dir(resume_id: uuid.UUID) -> Path:
    return STORAGE_ROOT / "resumes" / str(resume_id)


def _tailored_dir(resume_id: uuid.UUID, job_id: uuid.UUID) -> Path:
    return STORAGE_ROOT / "tailored" / str(resume_id) / str(job_id)


def file_kind_from_filename(filename: str, content_type: str | None) -> str:
    lower = (filename or "").lower()
    if lower.endswith(".pdf") or content_type == "application/pdf":
        return "pdf"
    if lower.endswith(".docx") or content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return "docx"
    return "txt"


def extension_for_kind(file_kind: str) -> str:
    return {"pdf": ".pdf", "docx": ".docx"}.get(file_kind, ".txt")


def save_original(resume_id: uuid.UUID, file_kind: str, data: bytes) -> str:
    dest_dir = _resume_dir(resume_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    rel = f"resumes/{resume_id}/original{extension_for_kind(file_kind)}"
    path = STORAGE_ROOT / rel
    path.write_bytes(data)
    return rel


def save_tailored_docx(resume_id: uuid.UUID, job_id: uuid.UUID, data: bytes) -> str:
    dest_dir = _tailored_dir(resume_id, job_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    rel = f"tailored/{resume_id}/{job_id}/tailored.docx"
    path = STORAGE_ROOT / rel
    path.write_bytes(data)
    return rel


def resolve_storage_path(rel_path: str) -> Path:
    path = (STORAGE_ROOT / rel_path).resolve()
    if not str(path).startswith(str(STORAGE_ROOT.resolve())):
        raise ValueError("Invalid storage path")
    return path


def delete_resume_files(resume_id: uuid.UUID) -> None:
    resume_path = _resume_dir(resume_id)
    if resume_path.exists():
        for child in resume_path.iterdir():
            child.unlink(missing_ok=True)
        resume_path.rmdir()


def delete_tailored_files(resume_id: uuid.UUID, job_id: uuid.UUID) -> None:
    tailored_path = _tailored_dir(resume_id, job_id)
    if tailored_path.exists():
        for child in tailored_path.iterdir():
            child.unlink(missing_ok=True)
        tailored_path.rmdir()
        # Remove empty parent dirs up to tailored/{resume_id}
        parent = tailored_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
