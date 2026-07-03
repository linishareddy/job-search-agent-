"""Scheduler entry point — run as: python -m config.scheduler"""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.logging import setup_logging
from config.settings import settings

logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncIOScheduler:
    return AsyncIOScheduler(timezone="UTC")


async def run_due_searches() -> None:
    """Check which saved searches are due and run them."""
    from config.database import AsyncSessionLocal
    from repositories.saved_search_repository import SavedSearchRepository
    from services.pipeline.orchestrator import PipelineOrchestrator

    async with AsyncSessionLocal() as session:
        repo = SavedSearchRepository(session)
        due_searches = await repo.get_due_searches()

    logger.info(f"Scheduler tick: {len(due_searches)} search(es) due")

    for search in due_searches:
        try:
            async with AsyncSessionLocal() as session:
                orchestrator = PipelineOrchestrator(session)
                await orchestrator.run(str(search.id))
                # Repositories only flush(); outside the API's get_db dependency the
                # session never commits on close, so scheduled runs must commit here.
                await session.commit()
            await asyncio.sleep(2)  # stagger Groq calls
        except Exception as e:
            logger.error(f"Pipeline failed for search {search.id}: {e}")


async def main() -> None:
    setup_logging()
    scheduler = build_scheduler()

    # Run every 30 minutes — the system heartbeat
    scheduler.add_job(
        run_due_searches,
        "interval",
        minutes=settings.scheduler_min_interval_minutes,
        id="check_due_searches",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),  # run immediately on start
    )

    scheduler.start()
    logger.info("Scheduler started — checking every %d minutes", settings.scheduler_min_interval_minutes)

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
