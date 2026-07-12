import uuid
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
from core.security import hash_password
from exceptions.handlers import register_exception_handlers
from routes import searches, companies, notifications, health, resumes, applications, analytics, auth, auto_apply


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
        # Mirrors alembic/versions/009_multi_user_email_tailoring_autoapply.py — the
        # `user` and `resume_tailoring` tables are brand new so create_all() above
        # already created them; only columns added to pre-existing tables need the
        # explicit ADD COLUMN IF NOT EXISTS treatment used throughout this block.
        await conn.execute(
            text('ALTER TABLE resume ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE')
        )
        await conn.execute(
            text('ALTER TABLE saved_search ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE')
        )
        await conn.execute(
            text('ALTER TABLE job_application ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE')
        )
        await conn.execute(
            text("ALTER TABLE job_application ADD COLUMN IF NOT EXISTS auto_prepared BOOLEAN NOT NULL DEFAULT false")
        )
        await conn.execute(text("ALTER TABLE job_application ADD COLUMN IF NOT EXISTS match_score FLOAT"))
        await conn.execute(text("ALTER TABLE job_application ADD COLUMN IF NOT EXISTS cover_letter TEXT"))
        await conn.execute(text("ALTER TABLE job_application ADD COLUMN IF NOT EXISTS tailored_resume TEXT"))

        # job_application used to be unique on job_id alone (one tracker card per job,
        # globally). Multi-user ownership needs unique(user_id, job_id) instead so two
        # users can each track the same job independently.
        await conn.execute(text("ALTER TABLE job_application DROP CONSTRAINT IF EXISTS job_application_job_id_key"))
        await conn.execute(text("""
            DO $$
            BEGIN
                ALTER TABLE job_application ADD CONSTRAINT uq_user_job_application UNIQUE (user_id, job_id);
            EXCEPTION
                WHEN duplicate_table THEN NULL;
            END $$;
        """))

        # Seed a default user (unusable random password — nobody logs in as this
        # account) so resumes/searches/applications created before auth existed have
        # an owner, then backfill those pre-existing rows onto it.
        # Explicit values for every NOT NULL column: the model's Python-side
        # default=/False only apply via the ORM, not this raw SQL insert.
        await conn.execute(
            text('INSERT INTO "user" '
                 '(id, email, hashed_password, is_active, email_enabled, '
                 ' auto_apply_enabled, auto_apply_min_score, auto_apply_max_per_run) '
                 'VALUES (gen_random_uuid(), :email, :hashed_password, true, true, '
                 '        false, 0.7, 5) '
                 'ON CONFLICT (email) DO NOTHING'),
            {"email": settings.seed_user_email, "hashed_password": hash_password(uuid.uuid4().hex)},
        )
        for table in ("resume", "saved_search", "job_application"):
            await conn.execute(
                text(f'UPDATE {table} SET user_id = (SELECT id FROM "user" WHERE email = :email) '
                     f'WHERE user_id IS NULL'),
                {"email": settings.seed_user_email},
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
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(auto_apply.router, prefix="/api/v1", tags=["auto-apply"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
