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


async def run_auto_apply() -> None:
    """Check every auto-apply-enabled user and prepare tailored resumes/cover
    letters for their best new job matches. Mirrors run_due_searches: each user
    gets its own session/commit so one user's failure can't roll back another's."""
    from config.database import AsyncSessionLocal
    from repositories.user_repository import UserRepository
    from services.auto_apply_service import AutoApplyService

    async with AsyncSessionLocal() as session:
        users = await UserRepository(session).get_auto_apply_enabled()

    logger.info(f"Auto-apply tick: {len(users)} user(s) opted in")

    for user in users:
        try:
            async with AsyncSessionLocal() as session:
                # Re-fetch inside this session — the user row from the lookup above
                # belongs to a session that's already closed.
                fresh_user = await UserRepository(session).get_by_id(user.id)
                if not fresh_user:
                    continue
                service = AutoApplyService(session)
                prepared = await service.run_for_user(fresh_user)
                # Same rule as run_due_searches: repositories only flush(), so this
                # session must commit itself outside the API's get_db dependency.
                await session.commit()
            if prepared:
                logger.info(f"Auto-apply: prepared {len(prepared)} application(s) for user {user.id}")
            await asyncio.sleep(2)  # stagger Groq calls
        except Exception as e:
            logger.error(f"Auto-apply failed for user {user.id}: {e}")


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

    # Run every 15 minutes (configurable) — assisted auto-apply
    scheduler.add_job(
        run_auto_apply,
        "interval",
        minutes=settings.auto_apply_interval_minutes,
        id="auto_apply",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )

    scheduler.start()
    logger.info("Scheduler started — checking every %d minutes", settings.scheduler_min_interval_minutes)
    logger.info("Auto-apply checking every %d minutes", settings.auto_apply_interval_minutes)

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
