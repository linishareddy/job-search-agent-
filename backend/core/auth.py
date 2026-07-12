from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from core.security import decode_token
from exceptions.handlers import AuthError
from models.user import User
from repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthError("Missing bearer token")

    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise AuthError("Invalid or expired token")

    user = await UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AuthError("User not found or inactive")

    return user
