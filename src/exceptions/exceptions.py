"""Exceptions module."""

from typing import Any


class BaseApplicationException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class PackageVersionNotFoundError(Exception):
    def __init__(self, message: str = "Version not found in pyproject.toml") -> None:
        self.message: str = message
        super().__init__(self.message)


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
            message=message,
            code="INVALID_STATE_TRANSITION",
            details=details,
            status_code=400,  # Bad Request - business rule violation
        )
