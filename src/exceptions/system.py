"""Exceptions module."""

from http import HTTPStatus
from typing import Any

from ..data.enums import ErrorCode
from .base import BaseApplicationException


class ExternalServiceException(BaseApplicationException):
    """Raised when an infrastructure-related error occurs."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR.code,
            details=details,
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class InvalidStateTransitionError(BaseApplicationException):
    """Raised when attempting an invalid state transition."""

    def __init__(
        self,
        message: str,
        current_state: str | None = None,
        attempted_state: str | None = None,
    ):
        details = {}
        if current_state:
            details["current_state"] = current_state
        if attempted_state:
            details["attempted_state"] = attempted_state

        super().__init__(
            code=ErrorCode.INVALID_STATE_TRANSITION.code,
            message=message,
            details=details,
            status_code=ErrorCode.INVALID_STATE_TRANSITION.status,
        )


class PackageVersionNotFoundError(Exception):
    def __init__(self, message: str = "Version not found in pyproject.toml") -> None:
        self.message: str = message
        super().__init__(self.message)


class ResourceNotFoundError(BaseApplicationException):
    """Raised when a business-related resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: int | None = None,
        **extra_details,
    ):
        details: dict[str, Any] = {"resource_type": resource_type, **extra_details}

        if resource_id is not None:
            details[f"{resource_type}_id"] = resource_id
            message = f"{resource_type.replace('_', ' ').title()} with ID {resource_id} not found"
        else:
            message = f"{resource_type.replace('_', ' ').title()} not found"

        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND.code,
            details=details,
            message=message,
            status_code=ErrorCode.RESOURCE_NOT_FOUND.status,
        )
