import re


_COMPANY_STRIP = re.compile(
    r"\b(inc|llc|ltd|limited|corp|corporation|co|company|group|holdings|technologies|tech|solutions|services)\b",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")
_NON_ALPHA = re.compile(r"[^a-z0-9\s]")


def normalize_company(name: str) -> str:
    name = name.lower()
    name = _COMPANY_STRIP.sub("", name)
    name = _NON_ALPHA.sub("", name)
    name = _WHITESPACE.sub(" ", name).strip()
    return name


def normalize_title(title: str) -> str:
    title = title.lower()
    title = _NON_ALPHA.sub("", title)
    title = _WHITESPACE.sub(" ", title).strip()
    return title


def normalize_work_mode(text: str) -> str | None:
    """Infer work_mode from a raw text snippet."""
    text_lower = text.lower()
    if any(w in text_lower for w in ("remote", "work from home", "wfh", "telecommute")):
        if any(w in text_lower for w in ("hybrid", "part remote", "partially remote")):
            return "hybrid"
        return "remote"
    if any(w in text_lower for w in ("hybrid",)):
        return "hybrid"
    if any(w in text_lower for w in ("on-site", "onsite", "in-office", "in office", "on site")):
        return "onsite"
    return None
