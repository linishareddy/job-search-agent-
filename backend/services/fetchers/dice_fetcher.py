import logging
from datetime import datetime, timezone

from constants.sources import DICE, SOURCE_RESULT_CAPS
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher, build_search_queries
from services.fetchers.dice_mcp_client import search_jobs
from services.fetchers.linkedin_location import is_us_job_location, resolve_scrape_location
from utils.salary_extractor import extract_salary

logger = logging.getLogger(__name__)


def _workplace_types(work_mode: str | None) -> list[str] | None:
    if work_mode == "remote":
        return ["Remote"]
    if work_mode == "hybrid":
        return ["Hybrid"]
    if work_mode == "onsite":
        return ["On-Site"]
    return None


def _dice_location(search: SavedSearchResponse) -> str:
    if search.work_mode == "remote":
        return "remote"
    return resolve_scrape_location(search.location)


class DiceFetcher(BaseJobFetcher):
    """Fetch US tech jobs from Dice via their official MCP server."""

    source_name = DICE

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        cap = SOURCE_RESULT_CAPS[DICE]
        keyword = build_search_queries(search, expansion)[0]
        location = _dice_location(search)
        args: dict = {
            "keyword": keyword,
            "location": location,
            "jobs_per_page": min(cap, 100),
            "page_number": 1,
            "posted_date": "SEVEN",
            "radius": 30,
            "radius_unit": "mi",
        }
        workplace = _workplace_types(search.work_mode)
        if workplace:
            args["workplace_types"] = workplace

        try:
            payload = await search_jobs(**args)
        except Exception as e:
            raise SourceFetchError(DICE, str(e)) from e

        raw_items = payload.get("data") or []
        jobs: list[JobRaw] = []
        seen_ids: set[str] = set()

        for item in raw_items:
            job = self._map(item)
            if not job or not job.external_id or job.external_id in seen_ids:
                continue
            if job.location and not is_us_job_location(job.location):
                continue
            seen_ids.add(job.external_id)
            jobs.append(job)
            if len(jobs) >= cap:
                break

        logger.info(f"Dice: fetched {len(jobs)} jobs")
        return jobs

    def _map(self, item: dict) -> JobRaw | None:
        title = (item.get("title") or "").strip()
        company = (item.get("companyName") or "").strip()
        apply_url = (item.get("detailsPageUrl") or "").strip()
        external_id = (item.get("guid") or item.get("id") or apply_url or "").strip()
        if not title or not company or not apply_url:
            return None

        location_obj = item.get("jobLocation") or {}
        location = location_obj.get("displayName") if isinstance(location_obj, dict) else None
        if not location and item.get("isRemote"):
            location = "Remote"

        work_mode = None
        if item.get("isRemote"):
            work_mode = "remote"
        else:
            types = item.get("workplaceTypes") or []
            if "Hybrid" in types:
                work_mode = "hybrid"
            elif "On-Site" in types:
                work_mode = "onsite"

        salary_text = (item.get("salary") or "").strip() or None
        salary_min, salary_max = extract_salary(salary_text)

        posted_at = None
        if item.get("postedDate"):
            try:
                posted_at = datetime.fromisoformat(str(item["postedDate"]).replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        description = (item.get("summary") or "").strip() or None

        return JobRaw(
            external_id=external_id,
            source=DICE,
            title=title,
            company_name=company,
            location=location,
            work_mode=work_mode,
            employment_type=(item.get("employmentType") or "").strip() or None,
            salary_text=salary_text,
            salary_min=salary_min,
            salary_max=salary_max,
            description=description,
            apply_url=apply_url,
            posted_at=posted_at,
        )
