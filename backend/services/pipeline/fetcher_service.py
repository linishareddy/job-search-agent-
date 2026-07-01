import asyncio
import logging

from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.adzuna_fetcher import AdzunaFetcher
from services.fetchers.ashby_fetcher import AshbyFetcher
from services.fetchers.greenhouse_fetcher import GreenhouseFetcher
from services.fetchers.jooble_fetcher import JoobleFetcher
from services.fetchers.lever_fetcher import LeverFetcher
from services.fetchers.remotive_fetcher import RemotiveFetcher

logger = logging.getLogger(__name__)

_FETCHERS = [
    AdzunaFetcher(),
    JoobleFetcher(),
    RemotiveFetcher(),
    GreenhouseFetcher(),
    LeverFetcher(),
    AshbyFetcher(),
]


async def fetch_all_sources(search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
    """Fetch from all 6 sources in parallel. Individual source failures are logged and skipped."""

    async def safe_fetch(fetcher, search, expansion):
        try:
            return await fetcher.fetch(search, expansion)
        except Exception as e:
            logger.error(f"Source {fetcher.source_name} failed: {e}")
            return []

    results = await asyncio.gather(*[safe_fetch(f, search, expansion) for f in _FETCHERS])

    all_jobs: list[JobRaw] = []
    for batch in results:
        all_jobs.extend(batch)

    logger.info(f"Total raw jobs fetched across all sources: {len(all_jobs)}")
    return all_jobs
