import logging

from schemas.saved_search import CompanySlug
from schemas.search_intent import ParsedSearchIntent
from services.groq_service import GroqService

logger = logging.getLogger(__name__)

_WORK_MODES = {"remote", "hybrid", "onsite", "any"}
_EXPERIENCE_LEVELS = {"entry", "mid", "senior", "lead", "any"}
_EMPLOYMENT_TYPES = {"full_time", "part_time", "contract", "any"}

# Same sanity bounds as utils/salary_extractor.extract_salary
_SALARY_MIN_FLOOR = 1_000
_SALARY_MAX_CEILING = 2_000_000


def _normalize_enum(value, allowed: set[str]) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized if normalized in allowed else None


def _sane_salary(value) -> int | None:
    if not isinstance(value, (int, float)):
        return None
    value = int(value)
    if value < _SALARY_MIN_FLOOR or value > _SALARY_MAX_CEILING:
        return None
    return value


class SearchIntentService:
    def __init__(self):
        self._groq = GroqService()

    async def parse(self, text: str) -> ParsedSearchIntent:
        """Parse free-text search intent via Groq and normalize it into a safe, saveable shape."""
        raw = await self._groq.parse_search_intent(text)

        job_title = (raw.get("job_title") or text.strip()[:256]).strip()
        field_domain = (raw.get("field_domain") or text.strip()).strip()
        name = (raw.get("name") or job_title).strip()[:256]

        work_mode = _normalize_enum(raw.get("work_mode"), _WORK_MODES)
        experience_level = _normalize_enum(raw.get("experience_level"), _EXPERIENCE_LEVELS)
        employment_type = _normalize_enum(raw.get("employment_type"), _EMPLOYMENT_TYPES)

        salary_min = _sane_salary(raw.get("salary_min"))
        salary_max = _sane_salary(raw.get("salary_max"))
        if salary_min and salary_max and salary_min > salary_max:
            salary_min, salary_max = salary_max, salary_min

        company_slugs = []
        for c in raw.get("company_slugs") or []:
            try:
                company_slugs.append(CompanySlug(**c))
            except Exception:
                logger.warning(f"Dropping malformed company_slug from Groq output: {c}")

        confidence = raw.get("confidence", 0.0)
        confidence = max(0.0, min(1.0, float(confidence))) if isinstance(confidence, (int, float)) else 0.0

        ambiguities = [a for a in (raw.get("ambiguities") or []) if isinstance(a, str)]

        return ParsedSearchIntent(
            job_title=job_title,
            field_domain=field_domain,
            name=name,
            location=raw.get("location") or None,
            work_mode=work_mode,
            experience_level=experience_level,
            employment_type=employment_type,
            salary_min=salary_min,
            salary_max=salary_max,
            company_slugs=company_slugs,
            confidence=confidence,
            ambiguities=ambiguities,
            raw_text=text,
        )
