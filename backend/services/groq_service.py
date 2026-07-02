import json
import logging
from typing import Any

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import settings
from exceptions.handlers import GroqError

logger = logging.getLogger(__name__)

_FAST_MODEL = "llama-3.1-8b-instant"       # field expansion — simple structured task
_SMART_MODEL = "llama-3.3-70b-versatile"   # job enrichment — nuanced relevance judgment


class GroqService:
    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _complete(self, model: str, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    async def expand_field_domain(self, job_title: str, field_domain: str) -> dict[str, Any]:
        """Call Groq to expand free-text field/domain into keywords, negatives, related titles."""
        from prompts.field_domain_expansion import SYSTEM_PROMPT, USER_TEMPLATE

        user_msg = USER_TEMPLATE.format(job_title=job_title, field_domain=field_domain)
        try:
            raw = await self._complete(_FAST_MODEL, SYSTEM_PROMPT, user_msg)
            return json.loads(raw)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Groq field expansion failed: {e}")
            # Graceful fallback so the pipeline can continue without expansion
            return {
                "search_queries": [f"{job_title} {field_domain}"],
                "primary_keywords": [job_title],
                "negative_keywords": [],
                "related_titles": [],
                "ideal_profile": f"{job_title} professional in the {field_domain} field.",
            }

    async def parse_search_intent(self, text: str) -> dict[str, Any]:
        """Call Groq to parse a free-text job search description into structured search fields."""
        from prompts.search_intent_parser import SYSTEM_PROMPT, USER_TEMPLATE

        user_msg = USER_TEMPLATE.format(text=text)
        try:
            raw = await self._complete(_FAST_MODEL, SYSTEM_PROMPT, user_msg)
            return json.loads(raw)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Groq search intent parse failed: {e}")
            # Graceful fallback: treat the whole text as the job title, flag low confidence
            return {
                "job_title": text.strip()[:256],
                "field_domain": text.strip(),
                "name": text.strip()[:256],
                "location": None,
                "work_mode": "any",
                "experience_level": "any",
                "employment_type": "any",
                "salary_min": None,
                "salary_max": None,
                "company_slugs": [],
                "confidence": 0.0,
                "ambiguities": ["Automatic parsing failed — please review all fields carefully."],
            }

    async def enrich_jobs(
        self,
        jobs: list[dict],
        job_title: str,
        field_domain: str,
        experience_level: str,
    ) -> list[dict[str, Any]]:
        """Batch-enrich up to 30 jobs with summary, skills, work_mode, salary, relevance_score."""
        from prompts.job_enrichment import SYSTEM_PROMPT, USER_TEMPLATE

        jobs_json = json.dumps(
            [{"idx": i, "title": j["title"], "company": j["company_name"], "description": (j.get("description") or "")[:800]} for i, j in enumerate(jobs)],
            indent=None,
        )
        user_msg = USER_TEMPLATE.format(
            job_title=job_title,
            field_domain=field_domain,
            experience_level=experience_level or "any",
            jobs_json=jobs_json,
        )

        try:
            raw = await self._complete(_SMART_MODEL, SYSTEM_PROMPT, user_msg)
            results = json.loads(raw)
            if not isinstance(results, list):
                raise ValueError("Expected JSON array")
            return results
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Groq enrichment parse failed: {e}\nRaw: {raw[:500]}")
            return []
        except Exception as e:
            logger.error(f"Groq enrichment call failed: {e}")
            raise GroqError(str(e)) from e
