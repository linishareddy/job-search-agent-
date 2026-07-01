import hashlib

from utils.text_normalizer import normalize_company, normalize_title


def compute_fingerprint(company_name: str, title: str) -> str:
    """SHA-256 fingerprint for exact job deduplication."""
    key = f"{normalize_company(company_name)}|{normalize_title(title)}"
    return hashlib.sha256(key.encode()).hexdigest()[:64]
