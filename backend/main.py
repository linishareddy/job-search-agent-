from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config.database import engine, Base
from config.logging import setup_logging
from exceptions.handlers import register_exception_handlers
from routes import searches, companies, notifications, health


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
    yield


app = FastAPI(
    title="AI Job Search Agent",
    description="Automated job discovery across Adzuna, Jooble, Remotive, Greenhouse, Lever, Ashby",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(searches.router, prefix="/api/v1", tags=["searches"])
app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
