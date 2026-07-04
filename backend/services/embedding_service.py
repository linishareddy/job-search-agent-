import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load model once and cache globally. Thread-safe via lru_cache."""
    logger.info(f"Loading sentence-transformer model: {_MODEL_NAME}")
    return SentenceTransformer(_MODEL_NAME)


class EmbeddingService:
    """NumPy cosine similarity, not `job.embedding`'s ivfflat/pgvector index.

    Looked at moving this to SQL-level `<=>` per the audit's REC-17 and found it
    doesn't cleanly apply: every caller (dedup_service's within-batch near-dupe
    merge, scoring_service's pre-score ranking, resume_match_service's per-page
    match score) compares an already-small, already-in-memory set — either jobs
    freshly fetched this run and not yet persisted, or an already-paginated page
    of results — never "find the nearest jobs across the whole table." There's no
    top-K-over-the-full-table query in this codebase for the ivfflat index to
    accelerate. It stays defined (harmless) for if/when a real semantic-search-
    across-all-jobs feature is added; forcing today's bounded, in-memory
    comparisons through SQL would restructure the pipeline/pagination flow for no
    actual performance win, and risk subtly changing match quality in the process.

    Real to-do if that day comes: thread the query vector into
    JobRepository.get_results_for_search() as an `ORDER BY job.embedding <=>
    :query_vec` clause, not a change here.
    """

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch embed texts. Returns list of 384-dim float vectors."""
        if not texts:
            return []
        model = _get_model()
        embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        norm_a = np.linalg.norm(va)
        norm_b = np.linalg.norm(vb)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(va, vb) / (norm_a * norm_b))
