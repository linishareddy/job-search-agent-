from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, hash_password, verify_password
from exceptions.handlers import AuthError, ConflictError, NotFoundError
from models.user import User
from repositories.user_repository import UserRepository
from schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserPreferencesUpdate, UserResponse


class AuthController:
    def __init__(self, session: AsyncSession):
        self._repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        existing = await self._repo.get_by_email(data.email)
        if existing:
            raise ConflictError("An account with this email already exists")
        user = await self._repo.create(
            email=data.email, hashed_password=hash_password(data.password), name=data.name
        )
        return TokenResponse(access_token=create_access_token(user.id))

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthError("Incorrect email or password")
        return TokenResponse(access_token=create_access_token(user.id))

    async def get_me(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def update_me(self, user: User, data: UserPreferencesUpdate) -> UserResponse:
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return UserResponse.model_validate(user)
        updated = await self._repo.update_preferences(user.id, updates)
        if not updated:
            raise NotFoundError("User", str(user.id))
        return UserResponse.model_validate(updated)
