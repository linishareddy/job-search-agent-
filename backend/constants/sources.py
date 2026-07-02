ADZUNA = "adzuna"
JOOBLE = "jooble"
REMOTIVE = "remotive"
GREENHOUSE = "greenhouse"
LEVER = "lever"
ASHBY = "ashby"

BREADTH_SOURCES = [ADZUNA, JOOBLE, REMOTIVE]
DEPTH_SOURCES = [GREENHOUSE, LEVER, ASHBY]
ALL_SOURCES = BREADTH_SOURCES + DEPTH_SOURCES

# Per-source result caps to stay within free-tier rate limits
SOURCE_RESULT_CAPS = {
    ADZUNA: 50,
    JOOBLE: 100,
    REMOTIVE: 100,
    GREENHOUSE: 500,  # spread across all tracked companies
    LEVER: 500,
    ASHBY: 500,
}

# Field expansion cache TTL in seconds (24 hours)
FIELD_EXPANSION_CACHE_TTL = 86400

# Jobs per Groq enrichment call — enrich_batch() chunks the full survivor pool into
# groups of this size and calls Groq once per chunk (sequentially), so every
# pre-scored survivor reaches Groq, not just the first chunk.
GROQ_ENRICHMENT_CHUNK_SIZE = 30

# Jobs in the pre-score stage kept before Groq enrichment
PRE_SCORE_TOP_K = 70

# Composite pre-score weights (must sum to 1.0) — cosine weighted highest so semantic
# similarity drives ranking more than raw keyword overlap.
BM25_WEIGHT = 0.25
COSINE_WEIGHT = 0.55
RECENCY_WEIGHT = 0.20

# Absolute cosine-similarity floor — jobs below this are dropped entirely before the
# top-K cut, so a weak candidate pool isn't padded with irrelevant jobs just to fill
# quota. Starting value, not empirically validated yet — tune from logged score
# distributions (see scoring_service.py's "Semantic floor" log line).
MIN_SEMANTIC_SIMILARITY = 0.30

# Cosine similarity threshold above which two jobs are treated as duplicates.
# Different concept from MIN_SEMANTIC_SIMILARITY above: this compares job-vs-job for
# near-duplicate merging (dedup_service.py), not query-vs-job for relevance.
VECTOR_DEDUP_THRESHOLD = 0.85

# Groq relevance score (1-10) above which a job triggers a notification
NOTIFICATION_SCORE_THRESHOLD = 7.0
