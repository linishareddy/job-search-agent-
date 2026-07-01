import re
from typing import Optional


# Matches patterns like: $80k-$120k, $80,000–$120,000, $45/hr, 80000-120000
_SALARY_RE = re.compile(
    r"\$?\s*(?P<min>[\d,\.]+)\s*[kK]?\s*(?:[-–to]+\s*\$?\s*(?P<max>[\d,\.]+)\s*[kK]?)?"
    r"(?:\s*/?\s*(?P<period>hr|hour|yr|year|annual|annum|month|mo))?",
    re.IGNORECASE,
)


def _parse_value(raw: str, is_k: bool) -> int:
    raw = raw.replace(",", "").strip()
    value = float(raw)
    if is_k:
        value *= 1000
    return int(value)


def extract_salary(text: str | None) -> tuple[Optional[int], Optional[int]]:
    """Extract (salary_min, salary_max) in annual USD from a raw salary string.

    Returns (None, None) if nothing can be parsed.
    Hourly rates are annualized at 2080 hours/year.
    """
    if not text:
        return None, None

    match = _SALARY_RE.search(text)
    if not match:
        return None, None

    is_k = "k" in text[match.start():match.end()].lower()
    period = (match.group("period") or "").lower()

    try:
        salary_min = _parse_value(match.group("min"), is_k)
    except (TypeError, ValueError):
        return None, None

    salary_max: Optional[int] = None
    if match.group("max"):
        try:
            salary_max = _parse_value(match.group("max"), is_k)
        except (TypeError, ValueError):
            pass

    # Annualize hourly
    if "hr" in period or "hour" in period:
        salary_min = salary_min * 2080
        if salary_max:
            salary_max = salary_max * 2080

    # Monthly → annual
    if "mo" in period or "month" in period:
        salary_min = salary_min * 12
        if salary_max:
            salary_max = salary_max * 12

    # Sanity-check: reject implausible values
    if salary_min < 1000 or salary_min > 2_000_000:
        return None, None

    return salary_min, salary_max
