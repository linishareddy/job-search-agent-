"""Base fetcher for JobSpy boards (LinkedIn, Indeed)."""
import asyncio
import logging
from dataclasses import dataclass

from config.settings import settings
from constants.sources import SOURCE_RESULT_CAPS
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher, build_search_queries
from services.fetchers.jobspy_helpers import dataframe_to_jobs
from services.fetchers.linkedin_location import (
    is_us_job_location,
    resolve_scrape_location,
    scrape_location_for_site,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobSpySiteConfig:
    source: str
    jobspy_site: str
    us_location_filter: bool = False
    use_country_indeed: bool = False


class JobSpySiteFetcher(BaseJobFetcher):
    """Scrapes one JobSpy site and maps results to JobRaw."""

    def __init__(self, config: JobSpySiteConfig):
        self._config = config
        self.source_name = config.source

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        cap = SOURCE_RESULT_CAPS.get(self.source_name, 30)
        query = build_search_queries(search, expansion)[0]
        location = resolve_scrape_location(
            search.location,
            default=settings.jobspy_default_location,
        )
        scrape_location = scrape_location_for_site(location, self._config.jobspy_site)
        scrape_kwargs = self._build_scrape_kwargs(query, scrape_location, cap, search)

        def _scrape():
            from jobspy import scrape_jobs

            return scrape_jobs(**scrape_kwargs)

        try:
            df = await asyncio.to_thread(_scrape)
        except Exception as e:
            logger.error(f"{self.source_name}/JobSpy failed: {e}")
            return []

        if df is None or df.empty:
            logger.info(f"{self.source_name}: fetched 0 jobs")
            return []

        jobs = dataframe_to_jobs(df, self.source_name)
        if self._config.us_location_filter and settings.jobspy_us_only:
            before = len(jobs)
            jobs = [j for j in jobs if is_us_job_location(j.location)]
            if before != len(jobs):
                logger.info(f"{self.source_name}: US filter removed {before - len(jobs)} jobs")

        logger.info(f"{self.source_name}: fetched {len(jobs)} jobs")
        return jobs[:cap]

    def _build_scrape_kwargs(
        self, query: str, scrape_location: str, cap: int, search: SavedSearchResponse
    ) -> dict:
        kwargs: dict = {
            "site_name": [self._config.jobspy_site],
            "search_term": query,
            "location": scrape_location,
            "results_wanted": min(cap, 30),
            "hours_old": 168,
            "linkedin_fetch_description": False,
        }
        if self._config.use_country_indeed:
            kwargs["country_indeed"] = settings.jobspy_country_indeed
        if search.work_mode == "remote":
            kwargs["is_remote"] = True
        if settings.jobspy_proxy_list:
            kwargs["proxies"] = settings.jobspy_proxy_list
        return kwargs
