import logging
from datetime import datetime, timezone
from typing import Optional

from rank_bm25 import BM25Okapi

from constants.sources import (
    BM25_WEIGHT,
    COSINE_WEIGHT,
    MIN_SEMANTIC_SIMILARITY,
    PRE_SCORE_TOP_K,
    RECENCY_WEIGHT,
)
from services.embedding_service import EmbeddingService
from services.pipeline.dedup_service import DeduplicatedJob

logger = logging.getLogger(__name__)

_embedding_service = EmbeddingService()


def _recency_score(posted_at: Optional[datetime]) -> float:
    if not posted_at:
        return 0.5  # neutral when unknown
    now = datetime.now(tz=timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    days_old = max(0, (now - posted_at).days)
    return max(0.0, 1.0 - days_old / 14.0)


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def pre_score_and_rank(
    jobs: list[DeduplicatedJob],
    expansion: dict,
    job_title: str,
    field_domain: str,
) -> list[DeduplicatedJob]:
    """
    Score each job using BM25 + cosine similarity + recency, then return top-K.

    BM25 is built from job title + description, using a keyword-dense query text
    (rewards term frequency). Cosine is computed between a separate, sentence-like
    semantic query embedding (built from ideal_profile + search_queries — rewards
    meaning over exact wording) and each job's embedding. Jobs below
    MIN_SEMANTIC_SIMILARITY are dropped entirely before ranking, so a weak batch
    isn't padded with irrelevant jobs just to fill PRE_SCORE_TOP_K.
    """
    if not jobs:
        return []

    # Build two purpose-built query strings from expansion
    primary_keywords = expansion.get("primary_keywords", [])
    related_titles = expansion.get("related_titles", [])
    search_queries = expansion.get("search_queries", [])
    ideal_profile = expansion.get("ideal_profile", "")

    semantic_query_text = f"{job_title} {field_domain}. {ideal_profile} {' '.join(search_queries)}"
    bm25_query_text = (
        f"{job_title} {field_domain} {' '.join(primary_keywords)} "
        f"{' '.join(related_titles)} {' '.join(search_queries)}"
    )

    # --- BM25 ---
    corpus = [
        _tokenize(f"{j.title} {j.description or ''}")
        for j in jobs
    ]
    bm25 = BM25Okapi(corpus)
    query_tokens = _tokenize(bm25_query_text)
    bm25_scores = bm25.get_scores(query_tokens)

    bm25_max = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    bm25_norm = [s / bm25_max for s in bm25_scores]

    # --- Cosine similarity ---
    query_embedding = _embedding_service.embed_single(semantic_query_text)
    cosine_scores = [
        _embedding_service.cosine_similarity(query_embedding, j.embedding)
        if j.embedding else 0.0
        for j in jobs
    ]

    # --- Absolute semantic floor (applied before ranking, not after) ---
    kept_indices = [i for i, c in enumerate(cosine_scores) if c >= MIN_SEMANTIC_SIMILARITY]
    logger.info(
        f"Semantic floor: {len(jobs)} → {len(kept_indices)} passed "
        f"MIN_SEMANTIC_SIMILARITY={MIN_SEMANTIC_SIMILARITY}"
    )

    # --- Composite score ---
    scored: list[tuple[float, float, float, DeduplicatedJob]] = []
    for i in kept_indices:
        job = jobs[i]
        bm25_s = bm25_norm[i]
        cos_s = cosine_scores[i]
        rec_s = _recency_score(job.posted_at)
        composite = BM25_WEIGHT * bm25_s + COSINE_WEIGHT * cos_s + RECENCY_WEIGHT * rec_s
        scored.append((composite, bm25_s, cos_s, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:PRE_SCORE_TOP_K]

    logger.info(f"Pre-scoring: {len(jobs)} jobs → top {len(top)} selected")

    # Attach pre-scores to jobs for later storage
    result = []
    for composite, bm25_s, cos_s, job in top:
        job._pre_score = composite
        job._bm25_score = bm25_s
        job._cosine_score = cos_s
        result.append(job)

    return result
