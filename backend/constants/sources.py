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

# Max jobs passed to Groq for enrichment (keeps calls within free-tier tokens)
GROQ_ENRICHMENT_BATCH_SIZE = 30

# Jobs in the pre-score stage kept before Groq enrichment
PRE_SCORE_TOP_K = 50

# Cosine similarity threshold above which two jobs are treated as duplicates
VECTOR_DEDUP_THRESHOLD = 0.85

# Groq relevance score (1-10) above which a job triggers a notification
NOTIFICATION_SCORE_THRESHOLD = 7.0
