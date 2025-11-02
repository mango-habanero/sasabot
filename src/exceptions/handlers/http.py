from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import HTTPException
from starlette.responses import JSONResponse

from src.configuration import app_logger
from src.data.dtos.responses import ErrorResponse
from src.data.enums import ErrorCode


async def http_exception_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    error_reference = uuid4().hex
    app_logger.error(
        "HTTP error | Status: %s | Detail: %s | Ref: %s",
        exc.status_code,
        exc.detail,
        error_reference,
        extra={"error_reference": error_reference},
    )

    if exc.status_code == 400:
        error_code = ErrorCode.INVALID_ARGUMENTS
    elif exc.status_code == 404:
        error_code = ErrorCode.RESOURCE_NOT_FOUND
    else:
        error_code = ErrorCode.INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=error_code.code,
            message=exc.detail or error_code.message,
            error_reference=error_reference,
        ).model_dump(mode="json", exclude_none=True),
    )
