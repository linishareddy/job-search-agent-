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
