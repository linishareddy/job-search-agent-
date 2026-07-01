import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from repositories.ats_company_repository import AtsCompanyRepository
from schemas.ats_company import AtsCompanyCreate, AtsCompanyResponse


class CompanyController:
    def __init__(self, session: AsyncSession):
        self._repo = AtsCompanyRepository(session)

    async def list_companies(self) -> list[AtsCompanyResponse]:
        companies = await self._repo.get_all_active()
        return [AtsCompanyResponse.model_validate(c) for c in companies]

    async def add_company(self, data: AtsCompanyCreate) -> AtsCompanyResponse:
        company = await self._repo.create(data)
        return AtsCompanyResponse.model_validate(company)

    async def delete_company(self, company_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(company_id)
        if not deleted:
            raise NotFoundError("AtsCompany", str(company_id))
