import asyncio
import logging

from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.adzuna_fetcher import AdzunaFetcher
from services.fetchers.arbeitnow_fetcher import ArbeitnowFetcher
from services.fetchers.ashby_fetcher import AshbyFetcher
from services.fetchers.dice_fetcher import DiceFetcher
from services.fetchers.greenhouse_fetcher import GreenhouseFetcher
from services.fetchers.jooble_fetcher import JoobleFetcher
from services.fetchers.jobspy_fetchers import ALL_JOBSPY_FETCHERS
from services.fetchers.lever_fetcher import LeverFetcher
from services.fetchers.remoteok_fetcher import RemoteOKFetcher
from services.fetchers.remotive_fetcher import RemotiveFetcher

logger = logging.getLogger(__name__)

_FETCHERS = [
    AdzunaFetcher(),
    JoobleFetcher(),
    RemotiveFetcher(),
    RemoteOKFetcher(),
    ArbeitnowFetcher(),
    DiceFetcher(),
    *ALL_JOBSPY_FETCHERS,
    GreenhouseFetcher(),
    LeverFetcher(),
    AshbyFetcher(),
]


async def fetch_all_sources(
    search: SavedSearchResponse, expansion: dict
) -> tuple[list[JobRaw], dict[str, dict]]:
    """Fetch from all sources in parallel. Individual source failures are logged and skipped.

    Returns (jobs, stats) where stats maps source name to
    {"fetched": int, "error": str | None} so each run record whether an empty source
    had no matches or actually failed.
    """
    stats: dict[str, dict] = {}

    async def safe_fetch(fetcher, search, expansion):
        try:
            batch = await fetcher.fetch(search, expansion)
            stats[fetcher.source_name] = {"fetched": len(batch), "error": None}
            return batch
        except Exception as e:
            logger.error(f"Source {fetcher.source_name} failed: {e}")
            stats[fetcher.source_name] = {"fetched": 0, "error": str(e)[:500]}
            return []

    results = await asyncio.gather(*[safe_fetch(f, search, expansion) for f in _FETCHERS])

    all_jobs: list[JobRaw] = []
    for batch in results:
        all_jobs.extend(batch)

    logger.info(f"Total raw jobs fetched across all sources: {len(all_jobs)}")
    return all_jobs, stats
