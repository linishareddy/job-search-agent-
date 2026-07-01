from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import engine, Base
from config.logging import setup_logging
from exceptions.handlers import register_exception_handlers
from routes import searches, jobs, companies, notifications, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
