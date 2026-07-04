"""Pipeline orchestrator — sequences all 11 steps per search run."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from constants.sources import NOTIFICATION_SCORE_THRESHOLD
from repositories.ats_company_repository import AtsCompanyRepository
from repositories.job_repository import JobRepository
from repositories.notification_repository import NotificationRepository
from repositories.saved_search_repository import SavedSearchRepository
from repositories.search_run_repository import SearchRunRepository
from services.pipeline import fetcher_service, normalizer_service
from services.pipeline.dedup_service import dedup_in_memory
from services.pipeline.enrichment_service import enrich_batch
from services.pipeline.scoring_service import pre_score_and_rank
from services.groq_service import GroqService
from utils.fingerprint import compute_fingerprint

logger = logging.getLogger(__name__)

_groq = GroqService()

# Field expansion cache TTL in hours (Groq is called again after this)
_EXPANSION_CACHE_TTL_HOURS = 24


class PipelineOrchestrator:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._search_repo = SavedSearchRepository(session)
        self._job_repo = JobRepository(session)
        self._run_repo = SearchRunRepository(session)
        self._notif_repo = NotificationRepository(session)

    async def create_run(self, search_id: str):
        """Validate the search and create its SearchRun row, committing immediately
        so the run (and each stage update during _execute) is visible to other DB
        connections — e.g. a browser polling for progress — as soon as it happens,
        rather than only once the whole pipeline finishes.

        Returns (search, run) or (None, None) if the search doesn't exist / is paused.
        """
        sid = uuid.UUID(search_id)
        search = await self._search_repo.get_by_id(sid)
        if not search or not search.is_active:
            logger.warning(f"Search {search_id} not found or inactive — skipping")
            return None, None
        run = await self._run_repo.create(sid)
        await self._session.commit()
        return search, run

    async def run(self, search_id: str) -> uuid.UUID:
        """Create the run and execute the full 11-step pipeline synchronously in
        the caller's session. Used by the scheduler, which already manages its own
        per-search session and commits — not used for API-triggered runs, which
        background the actual execution (see run_in_background below) so the HTTP
        request isn't held open for the pipeline's full duration.
        """
        search, run = await self.create_run(search_id)
        if not search:
            return uuid.UUID(search_id)
        await self.execute_safely(search, run)
        return run.id

    async def execute_safely(self, search, run) -> None:
        logger.info(f"[Run {run.id}] Starting pipeline for search '{search.name}'")
        try:
            await self._execute(search, run)
        except Exception as e:
            logger.error(f"[Run {run.id}] Pipeline failed: {e}", exc_info=True)
            await self._run_repo.fail(run.id, str(e))
            await self._session.commit()

    async def _execute(self, search, run) -> None:
        # ── Step 1: Field expansion (Groq, cached 24h) ──────────────────────────
        expansion = await self._get_expansion(search)
        await self._run_repo.update_stage(run.id, 1)

        # ── Step 2: Parallel fetch from all 6 sources ───────────────────────────
        from schemas.saved_search import CompanySlug, SavedSearchResponse
        search_schema = SavedSearchResponse.model_validate(search)

        # Merge the global ATS company watch-list into this search's slugs so
        # Greenhouse/Lever/Ashby cover every tracked company, not only those named
        # explicitly on the search itself.
        watchlist = await AtsCompanyRepository(self._session).get_all_active()
        seen = {(c.slug, c.source) for c in search_schema.company_slugs}
        search_schema.company_slugs += [
            CompanySlug(name=c.name, slug=c.slug, source=c.source)
            for c in watchlist
            if (c.slug, c.source) not in seen
        ]

        raw_jobs, source_stats = await fetcher_service.fetch_all_sources(search_schema, expansion)
        jobs_fetched = len(raw_jobs)
        logger.info(f"[Run {run.id}] Step 2: {jobs_fetched} raw jobs fetched")
        await self._run_repo.update_stage(run.id, 2)

        # ── Step 3: Normalize all to JobRaw schema ───────────────────────────────
        normalized = normalizer_service.normalize(raw_jobs)
        await self._run_repo.update_stage(run.id, 3)

        # ── Step 4: Negative keyword pre-filter ─────────────────────────────────
        filtered = normalizer_service.apply_negative_filter(
            normalized, expansion.get("negative_keywords", [])
        )

        if not filtered:
            await self._run_repo.complete(run.id, jobs_fetched, 0, 0, source_stats=source_stats)
            await self._search_repo.update_last_run(search.id)
            return

        await self._run_repo.update_stage(run.id, 4)

        # ── Step 5: Fingerprint dedup — skip jobs already in DB ─────────────────
        candidate_fps = [compute_fingerprint(job.company_name, job.title) for job in filtered]
        existing_fps = await self._job_repo.get_existing_fingerprints(candidate_fps)
        await self._run_repo.update_stage(run.id, 5)

        # ── Steps 6+7: Embed + vector dedup ────────────────────────────────────
        deduped = dedup_in_memory(filtered, existing_fps)

        if not deduped:
            await self._run_repo.complete(run.id, jobs_fetched, 0, 0, source_stats=source_stats)
            await self._search_repo.update_last_run(search.id)
            return

        # Steps 6+7 are one in-memory pass, so the stage index jumps straight to 7
        # ("Pre-score") rather than pausing at 6 ("Dedup semantic") — there's no
        # real checkpoint between them to report honestly.
        await self._run_repo.update_stage(run.id, 7)

        # ── Step 8: BM25 + cosine pre-score → top 30 ────────────────────────────
        top_jobs = pre_score_and_rank(
            deduped,
            expansion,
            job_title=search.job_title,
            field_domain=search.field_domain,
        )
        await self._run_repo.update_stage(run.id, 8)

        # ── Step 9: Groq batch enrichment (top 30 only) ─────────────────────────
        enriched = await enrich_batch(
            top_jobs,
            job_title=search.job_title,
            field_domain=search.field_domain,
            experience_level=search.experience_level or "any",
        )
        await self._run_repo.update_stage(run.id, 9)

        # ── Step 10: Upsert job records + search results ─────────────────────────
        previous_job_ids = await self._job_repo.get_previous_job_ids(search.id)
        new_count = 0

        for enriched_job in enriched:
            db_job = await self._job_repo.upsert_job(enriched_job)
            is_new = db_job.id not in previous_job_ids
            if is_new:
                new_count += 1

            await self._job_repo.upsert_search_result(
                job_id=db_job.id,
                search_id=search.id,
                run_id=run.id,
                relevance_score=enriched_job.relevance_score,
                bm25_score=enriched_job.bm25_score,
                cosine_score=enriched_job.cosine_score,
                match_reason=enriched_job.match_reason,
                gaps=enriched_job.gaps,
                is_new=is_new,
            )

        await self._run_repo.update_stage(run.id, 10)

        # ── Step 11: Notification if new high-scoring jobs found ─────────────────
        high_score_new = [
            j for j in enriched
            if j.relevance_score >= (NOTIFICATION_SCORE_THRESHOLD / 10.0)
        ]
        if high_score_new and new_count > 0:
            await self._notif_repo.create(
                search_id=search.id,
                run_id=run.id,
                message=f"'{search.name}': {new_count} new job(s) found, {len(high_score_new)} high-relevance",
                new_job_count=new_count,
            )

        # ── Finalize ─────────────────────────────────────────────────────────────
        await self._run_repo.complete(run.id, jobs_fetched, len(enriched), new_count, source_stats=source_stats)
        await self._search_repo.update_last_run(search.id)

        logger.info(
            f"[Run {run.id}] Completed: {jobs_fetched} fetched → "
            f"{len(enriched)} matched → {new_count} new"
        )

    async def _get_expansion(self, search) -> dict:
        """Return cached expansion or call Groq and cache the result."""
        now = datetime.now(timezone.utc)
        cache_valid = (
            search.field_expansion_cache
            and search.field_expansion_cached_at
            and (now - search.field_expansion_cached_at.replace(tzinfo=timezone.utc)).total_seconds()
            < _EXPANSION_CACHE_TTL_HOURS * 3600
        )

        if cache_valid:
            logger.debug(f"Using cached field expansion for search {search.id}")
            return search.field_expansion_cache

        logger.info(f"Calling Groq for field expansion: '{search.job_title}' in '{search.field_domain}'")
        expansion = await _groq.expand_field_domain(search.job_title, search.field_domain)
        await self._search_repo.cache_field_expansion(search.id, expansion)
        await self._session.refresh(search)
        return expansion


async def run_in_background(search_id: str, run_id: uuid.UUID) -> None:
    """Executes an already-created run on its own fresh session.

    API-triggered runs (POST /searches/{id}/run and /searches/from-text with
    run_immediately) schedule this via FastAPI's BackgroundTasks after creating
    the run row, instead of awaiting the pipeline inline — otherwise the request
    (and the frontend's progress polling, which only starts once that request
    resolves) would be blocked for the pipeline's full 1-5 minute duration.
    """
    from config.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        search_repo = SavedSearchRepository(session)
        run_repo = SearchRunRepository(session)
        search = await search_repo.get_by_id(uuid.UUID(search_id))
        run = await run_repo.get_latest_any(uuid.UUID(search_id))
        if not search or not run or run.id != run_id:
            logger.error(f"Background run {run_id}: search or run row not found")
            return
        orchestrator = PipelineOrchestrator(session)
        await orchestrator.execute_safely(search, run)
        # Safety net: unlike SearchRunRepository's writes, update_last_run() (and
        # anything else _execute touches) only flushes — there's no get_db/scheduler
        # caller here to commit it, so this session must do it itself.
        await session.commit()
