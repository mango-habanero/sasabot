"""System exception handlers."""

import logging
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.responses import JSONResponse

from src.data.dtos.responses import ErrorDetail, ErrorResponse
from src.data.enums import ErrorCode

logger = logging.getLogger(__name__)


async def http_exception_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    error_reference = uuid4().hex
    logger.error(
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


async def validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    error_reference = uuid4().hex
    errors = [
        ErrorDetail.of(
            field=".".join(map(str, error["loc"][1:])),
            message=error["msg"],
            rejected_value=str(error.get("input"))[:100]
            if error.get("input")
            else None,
        )
        for error in exc.errors()
    ]

    logger.warning(
        "Validation error | Ref: %s | Errors: %d",
        error_reference,
        len(errors),
        extra={"error_reference": error_reference},
    )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            code=ErrorCode.INVALID_ARGUMENTS.code,
            message=ErrorCode.INVALID_ARGUMENTS.message,
            errors=errors,
            error_reference=error_reference,
        ).model_dump(mode="json", exclude_none=True),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_reference = uuid4().hex
    logger.exception(
        "Unexpected error | Ref: %s | Path: %s",
        error_reference,
        request.url.path,
        exc_info=exc,
        extra={"error_reference": error_reference},
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=ErrorCode.INTERNAL_SERVER_ERROR.code,
            message=ErrorCode.INTERNAL_SERVER_ERROR.message,
            error_reference=error_reference,
        ).model_dump(mode="json", exclude_none=True),
    )
