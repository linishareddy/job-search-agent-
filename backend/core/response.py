from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


def ok(data: Any = None, message: str | None = None, total: int | None = None, page: int | None = None, page_size: int | None = None) -> dict:
    return ApiResponse(success=True, data=data, message=message, total=total, page=page, page_size=page_size).model_dump(exclude_none=True)


def error(message: str) -> dict:
    return ApiResponse(success=False, message=message).model_dump(exclude_none=True)
