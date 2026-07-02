"""Pipeline orchestrator — sequences all 11 steps per search run."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from constants.sources import NOTIFICATION_SCORE_THRESHOLD
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

    async def run(self, search_id: str) -> uuid.UUID:
        """Execute the full 11-step pipeline for one saved search.

        Returns the search_run.id for status polling.
        """
        sid = uuid.UUID(search_id)

        # Load search
        search = await self._search_repo.get_by_id(sid)
        if not search or not search.is_active:
            logger.warning(f"Search {search_id} not found or inactive — skipping")
            return sid

        # Create run record
        run = await self._run_repo.create(sid)
        logger.info(f"[Run {run.id}] Starting pipeline for search '{search.name}'")

        try:
            await self._execute(search, run)
        except Exception as e:
            logger.error(f"[Run {run.id}] Pipeline failed: {e}", exc_info=True)
            await self._run_repo.fail(run.id, str(e))

        return run.id

    async def _execute(self, search, run) -> None:
        # ── Step 1: Field expansion (Groq, cached 24h) ──────────────────────────
        expansion = await self._get_expansion(search)

        # ── Step 2: Parallel fetch from all 6 sources ───────────────────────────
        from schemas.saved_search import SavedSearchResponse
        search_schema = SavedSearchResponse.model_validate(search)
        raw_jobs = await fetcher_service.fetch_all_sources(search_schema, expansion)
        jobs_fetched = len(raw_jobs)
        logger.info(f"[Run {run.id}] Step 2: {jobs_fetched} raw jobs fetched")

        # ── Step 3: Normalize all to JobRaw schema ───────────────────────────────
        normalized = normalizer_service.normalize(raw_jobs)

        # ── Step 4: Negative keyword pre-filter ─────────────────────────────────
        filtered = normalizer_service.apply_negative_filter(
            normalized, expansion.get("negative_keywords", [])
        )

        if not filtered:
            await self._run_repo.complete(run.id, jobs_fetched, 0, 0)
            await self._search_repo.update_last_run(search.id)
            return

        # ── Step 5: Fingerprint dedup — skip jobs already in DB ─────────────────
        candidate_fps = [compute_fingerprint(job.company_name, job.title) for job in filtered]
        existing_fps = await self._job_repo.get_existing_fingerprints(candidate_fps)

        # ── Steps 6+7: Embed + vector dedup ────────────────────────────────────
        deduped = dedup_in_memory(filtered, existing_fps)

        if not deduped:
            await self._run_repo.complete(run.id, jobs_fetched, 0, 0)
            await self._search_repo.update_last_run(search.id)
            return

        # ── Step 8: BM25 + cosine pre-score → top 30 ────────────────────────────
        top_jobs = pre_score_and_rank(
            deduped,
            expansion,
            job_title=search.job_title,
            field_domain=search.field_domain,
        )

        # ── Step 9: Groq batch enrichment (top 30 only) ─────────────────────────
        enriched = await enrich_batch(
            top_jobs,
            job_title=search.job_title,
            field_domain=search.field_domain,
            experience_level=search.experience_level or "any",
        )

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
        await self._run_repo.complete(run.id, jobs_fetched, len(enriched), new_count)
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
