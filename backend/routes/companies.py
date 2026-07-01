import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.company_controller import CompanyController
from core.response import ok
from schemas.ats_company import AtsCompanyCreate

router = APIRouter(prefix="/companies")


@router.get("")
async def list_companies(db: AsyncSession = Depends(get_db)):
    ctrl = CompanyController(db)
    companies = await ctrl.list_companies()
    return ok(data=[c.model_dump() for c in companies], total=len(companies))


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_company(data: AtsCompanyCreate, db: AsyncSession = Depends(get_db)):
    ctrl = CompanyController(db)
    company = await ctrl.add_company(data)
    return ok(data=company.model_dump())


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ctrl = CompanyController(db)
    await ctrl.delete_company(company_id)
