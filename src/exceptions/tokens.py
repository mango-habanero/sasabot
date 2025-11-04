from http import HTTPStatus
from typing import Any

from src.data.enums import ErrorCode
from src.exceptions.base import BaseApplicationException


class TokenRefreshException(BaseApplicationException):
    """Raised when token refresh fails."""

    def __init__(
        self,
        message: str = "Failed to refresh token.",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR.code,
            details=details,
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
