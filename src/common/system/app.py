"""Application entrypoint."""

from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from src.api import api_router
from src.configuration import settings
from src.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.middleware import HttpRequestLoggingMiddleware


def create_app(
    *,
    title: str = "FastAPI",
    description: str = "",
    version: str,
    **kwargs: Any,
) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        **kwargs,
    )
    configure_exception_handlers(app)
    configure_middleware(app)
    configure_routes(app)
    return app


def configure_exception_handlers(app: FastAPI) -> FastAPI:
    """Configure exception handlers for the FastAPI application."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    return app


def configure_middleware(app: FastAPI):
    """Configure middleware for the FastAPI application."""
    app.add_middleware(HttpRequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


def configure_routes(app: FastAPI):
    """Configure routes for the FastAPI application."""
    app.include_router(api_router)
