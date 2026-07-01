import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ats_company import AtsCompany
from schemas.ats_company import AtsCompanyCreate


class AtsCompanyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: AtsCompanyCreate) -> AtsCompany:
        company = AtsCompany(**data.model_dump())
        self._session.add(company)
        await self._session.flush()
        return company

    async def get_all_active(self) -> list[AtsCompany]:
        result = await self._session.execute(
            select(AtsCompany).where(AtsCompany.is_active.is_(True)).order_by(AtsCompany.name)
        )
        return result.scalars().all()

    async def get_by_id(self, company_id: uuid.UUID) -> AtsCompany | None:
        result = await self._session.execute(
            select(AtsCompany).where(AtsCompany.id == company_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, company_id: uuid.UUID) -> bool:
        company = await self.get_by_id(company_id)
        if not company:
            return False
        await self._session.delete(company)
        await self._session.flush()
        return True
