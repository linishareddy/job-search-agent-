from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from constants.sources import ALL_SOURCES
from core.response import ok

router = APIRouter(prefix="/health")


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return ok(data={"database": db_status, "status": "running"})


@router.get("/sources")
async def source_health(db: AsyncSession = Depends(get_db)):
    """Return the latest run status per source (from recent search_runs)."""
    result = await db.execute(
        text("""
            SELECT source, COUNT(*) as total
            FROM job
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY source
        """)
    )
    rows = result.mappings().all()
    by_source = {row["source"]: row["total"] for row in rows}
    return ok(data={source: {"jobs_last_24h": by_source.get(source, 0)} for source in ALL_SOURCES})
