from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from config.database import engine, Base
from config.logging import setup_logging
from config.settings import settings
from core.rate_limit import limiter
from exceptions.handlers import register_exception_handlers
from routes import searches, companies, notifications, health, resumes, applications, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # TEMP: mirrors alembic/versions/002_phase2_match_reasoning.py — remove once a
        # real migration step runs at deploy time. create_all() only creates missing
        # tables, so already-existing tables need these backfilled explicitly.
        await conn.execute(text("ALTER TABLE job_search_result ADD COLUMN IF NOT EXISTS match_reason TEXT"))
        await conn.execute(text("ALTER TABLE job_search_result ADD COLUMN IF NOT EXISTS gaps TEXT"))
        # Mirrors alembic/versions/003_source_stats.py
        await conn.execute(text("ALTER TABLE search_run ADD COLUMN IF NOT EXISTS source_stats JSONB"))
        # Mirrors alembic/versions/004_posted_within_days.py
        await conn.execute(text("ALTER TABLE saved_search ADD COLUMN IF NOT EXISTS posted_within_days INTEGER"))
        # Mirrors alembic/versions/007_pipeline_stage_tracking.py
        await conn.execute(
            text("ALTER TABLE search_run ADD COLUMN IF NOT EXISTS current_stage_index INTEGER NOT NULL DEFAULT 0")
        )
        # Mirrors alembic/versions/008_missing_indexes.py — indexes the audit found
        # missing even in the original migration (job.source is grouped on in the
        # health endpoint; the FK columns had no index at all).
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_source ON job (source)"))
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_jsr_run ON job_search_result (run_id)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_notification_search ON notification (search_id)")
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notification_run ON notification (run_id)"))
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_search_run_status ON search_run (status, started_at)")
        )
    yield


app = FastAPI(
    title="AI Job Search Agent",
    description="Automated job discovery across Adzuna, Jooble, Remotive, Greenhouse, Lever, Ashby",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

register_exception_handlers(app)

app.include_router(searches.router, prefix="/api/v1", tags=["searches"])
app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(resumes.router, prefix="/api/v1", tags=["resumes"])
app.include_router(applications.router, prefix="/api/v1", tags=["applications"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
