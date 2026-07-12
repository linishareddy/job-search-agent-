import logging
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from constants.sources import REMOTEOK, SOURCE_RESULT_CAPS
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher
from services.fetchers.feed_filter import matches_keywords, search_query_list

logger = logging.getLogger(__name__)

_BASE_URL = "https://remoteok.com/api"
_HEADERS = {"User-Agent": "JobRadar/1.0 (job aggregator; attribution: remoteok.com)"}


class RemoteOKFetcher(BaseJobFetcher):
    source_name = REMOTEOK

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get_all(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0, headers=_HEADERS) as client:
            response = await client.get(_BASE_URL)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                return []
            # First element is a legal/attribution notice, not a job listing.
            return [item for item in data if isinstance(item, dict) and item.get("id")]

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        if search.work_mode == "onsite":
            return []

        cap = SOURCE_RESULT_CAPS[REMOTEOK]
        queries = search_query_list(search, expansion)

        try:
            raw_items = await self._get_all()
        except httpx.HTTPError as e:
            raise SourceFetchError(REMOTEOK, str(e)) from e

        jobs: list[JobRaw] = []
        seen_ids: set[str] = set()

        for item in raw_items:
            job = self._map(item)
            if not job.external_id or job.external_id in seen_ids:
                continue
            if not matches_keywords(
                " ".join(
                    [
                        job.title,
                        job.company_name,
                        job.description or "",
                        " ".join(item.get("tags") or []),
                    ]
                ),
                queries,
            ):
                continue
            seen_ids.add(job.external_id)
            jobs.append(job)
            if len(jobs) >= cap:
                break

        logger.info(f"RemoteOK: fetched {len(jobs)} jobs")
        return jobs

    def _map(self, item: dict) -> JobRaw:
        posted_at = None
        if item.get("date"):
            try:
                posted_at = datetime.fromtimestamp(int(item["date"]), tz=timezone.utc)
            except (TypeError, ValueError):
                pass

        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")
        salary_text = None
        if salary_min or salary_max:
            salary_text = f"${salary_min or ''}-${salary_max or ''}".replace("$-$", "")

        location = item.get("location") or "Remote"
        apply_url = item.get("url") or item.get("apply_url") or ""

        return JobRaw(
            external_id=str(item.get("id", "")),
            source=REMOTEOK,
            title=item.get("position") or item.get("title") or "",
            company_name=item.get("company") or "",
            location=location,
            work_mode="remote",
            salary_text=salary_text,
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            description=item.get("description"),
            apply_url=apply_url,
            posted_at=posted_at,
        )
