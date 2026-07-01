import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.saved_search import SavedSearch
from schemas.saved_search import SavedSearchCreate, SavedSearchUpdate


class SavedSearchRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: SavedSearchCreate) -> SavedSearch:
        search = SavedSearch(**data.model_dump())
        self._session.add(search)
        await self._session.flush()
        return search

    async def get_by_id(self, search_id: uuid.UUID) -> SavedSearch | None:
        result = await self._session.execute(
            select(SavedSearch).where(SavedSearch.id == search_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID) -> list[SavedSearch]:
        result = await self._session.execute(
            select(SavedSearch)
            .where(SavedSearch.user_id == user_id)
            .order_by(SavedSearch.created_at.desc())
        )
        return result.scalars().all()

    async def update(self, search_id: uuid.UUID, data: SavedSearchUpdate) -> SavedSearch | None:
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return await self.get_by_id(search_id)

        # If field_domain or job_title changed, invalidate field expansion cache
        if "field_domain" in updates or "job_title" in updates:
            updates["field_expansion_cache"] = None
            updates["field_expansion_cached_at"] = None

        await self._session.execute(
            update(SavedSearch)
            .where(SavedSearch.id == search_id)
            .values(**updates, updated_at=datetime.now(timezone.utc))
        )
        await self._session.flush()
        return await self.get_by_id(search_id)

    async def delete(self, search_id: uuid.UUID) -> bool:
        search = await self.get_by_id(search_id)
        if not search:
            return False
        await self._session.delete(search)
        await self._session.flush()
        return True

    async def get_due_searches(self) -> list[SavedSearch]:
        """Return active searches where last_run_at + poll_interval <= now."""
        from sqlalchemy import or_, func, text
        result = await self._session.execute(
            select(SavedSearch).where(
                SavedSearch.is_active.is_(True),
                or_(
                    SavedSearch.last_run_at.is_(None),
                    text(
                        "last_run_at + (poll_interval_minutes || ' minutes')::interval <= NOW()"
                    ),
                ),
            )
        )
        return result.scalars().all()

    async def update_last_run(self, search_id: uuid.UUID) -> None:
        await self._session.execute(
            update(SavedSearch)
            .where(SavedSearch.id == search_id)
            .values(last_run_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    async def cache_field_expansion(self, search_id: uuid.UUID, expansion: dict) -> None:
        await self._session.execute(
            update(SavedSearch)
            .where(SavedSearch.id == search_id)
            .values(
                field_expansion_cache=expansion,
                field_expansion_cached_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
