"""System error enumerations."""

from enum import Enum
from http import HTTPStatus


class ErrorCode(Enum):
    INTERNAL_SERVER_ERROR = (
        "INTERNAL_SERVER_ERROR",
        "An unexpected error occurred while processing your request. Please try again or contact support.",
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    INVALID_ARGUMENTS = (
        "INVALID_ARGUMENTS",
        "Request contains invalid or incomplete arguments.",
        HTTPStatus.BAD_REQUEST,
    )
    INVALID_STATE_TRANSITION = (
        "INVALID_STATE_TRANSITION",
        "The requested operation cannot be performed in the current state.",
        HTTPStatus.BAD_REQUEST,
    )
    RESOURCE_NOT_FOUND = (
        "RESOURCE_NOT_FOUND",
        "The specified resource does not exist.",
        HTTPStatus.NOT_FOUND,
    )

    def __init__(self, code: str, message: str, status: HTTPStatus):
        self._code = code
        self._message = message
        self._status = status

    @property
    def code(self) -> str:
        return self._code

    @property
    def message(self) -> str:
        return self._message

    @property
    def status(self) -> int:
        return self._status.value
