import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, email: str, hashed_password: str, name: str | None) -> User:
        user = User(email=email, hashed_password=hashed_password, name=name)
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[User]:
        result = await self._session.execute(select(User).where(User.is_active.is_(True)))
        return result.scalars().all()

    async def get_auto_apply_enabled(self) -> list[User]:
        result = await self._session.execute(
            select(User).where(User.is_active.is_(True), User.auto_apply_enabled.is_(True))
        )
        return result.scalars().all()

    async def update_preferences(self, user_id: uuid.UUID, updates: dict) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in updates.items():
            setattr(user, key, value)
        await self._session.flush()
        # Re-fetch so the server-side onupdate `updated_at` is loaded via async IO,
        # not lazily during (sync) pydantic serialization — see JobApplicationRepository.update.
        return await self.get_by_id(user_id)
