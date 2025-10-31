"""API response DTOs."""

from datetime import UTC, datetime
from typing import Generic, List, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.data.enums import ResponseStatus

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )

    status: ResponseStatus
    message: str
    data: T | None = None

    def model_dump(self, *args, **kwargs):
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(*args, **kwargs)

    @classmethod
    def success(cls, message: str, data: T) -> "BaseResponse[T]":
        return cls(status=ResponseStatus.SUCCESS, message=message, data=data)


class ErrorDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: str | None = None
    message: str
    rejected_value: str | None = None

    @classmethod
    def of(
        cls,
        field: str | None,
        message: str,
        rejected_value: str | None = None,
    ) -> "ErrorDetail":
        return cls(field=field, message=message, rejected_value=rejected_value)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: ResponseStatus = ResponseStatus.FAILED
    code: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    errors: List[ErrorDetail] = Field(default_factory=list)
    error_reference: str = Field(default_factory=lambda: uuid4().hex)

    @classmethod
    def from_exception(
        cls,
        code: str,
        message: str,
        errors: List[ErrorDetail] | None = None,
        error_reference: str | None = None,
    ) -> "ErrorResponse":
        return cls(
            code=code,
            message=message,
            errors=errors or [],
            error_reference=error_reference or uuid4().hex,
        )
