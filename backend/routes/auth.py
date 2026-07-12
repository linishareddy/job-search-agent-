from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.auth_controller import AuthController
from core.auth import get_current_user
from core.response import ok
from models.user import User
from schemas.user import LoginRequest, RegisterRequest, UserPreferencesUpdate

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    ctrl = AuthController(db)
    token = await ctrl.register(data)
    return ok(data=token.model_dump())


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    ctrl = AuthController(db)
    token = await ctrl.login(data)
    return ok(data=token.model_dump())


@router.get("/me")
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ctrl = AuthController(db)
    profile = await ctrl.get_me(user)
    return ok(data=profile.model_dump())


@router.patch("/me")
async def update_me(
    data: UserPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = AuthController(db)
    profile = await ctrl.update_me(user, data)
    return ok(data=profile.model_dump())
