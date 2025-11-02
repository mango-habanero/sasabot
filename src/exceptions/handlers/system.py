"""System exception handlers."""

from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from src.configuration import app_logger
from src.data.dtos.responses import ErrorDetail, ErrorResponse
from src.data.enums import ErrorCode


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

    app_logger.warning(
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
    app_logger.exception(
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
