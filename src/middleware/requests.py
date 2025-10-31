"""Request logging middleware."""

import time
import urllib.parse
from collections.abc import MutableMapping

import structlog
from asgi_correlation_id.context import correlation_id
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

access_logger = structlog.stdlib.get_logger("api.access")


# Adapted with thanks from: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
class HttpRequestLoggingMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _get_path_with_query_string(scope: MutableMapping) -> str:
        path_with_query_string = urllib.parse.quote(scope["path"])
        if scope["query_string"]:
            path_with_query_string = "{}?{}".format(
                path_with_query_string, scope["query_string"].decode("ascii")
            )
        return path_with_query_string

    async def dispatch(self, request: Request, call_next) -> Response:
        structlog.contextvars.clear_contextvars()

        request_id = correlation_id.get()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()
        response = Response("Internal Server Error", status_code=500)
        try:
            response = await call_next(request)
        except Exception:
            structlog.stdlib.get_logger("api.error").exception("Unhandled exception.")
            raise
        finally:
            client = request.client
            host = client.host if client else "unknown"
            port = client.port if client else 0

            method = request.method
            version = request.scope["http_version"]
            status_code = response.status_code
            url = self._get_path_with_query_string(request.scope)

            process_time = time.perf_counter_ns() - start_time
            event = f"{host}:{port} - '{method} {url} HTTP/{version}' {status_code}"
            access_logger.info(
                event,
                http={
                    "url": str(request.url),
                    "status_code": status_code,
                    "method": method,
                    "request_id": request_id,
                    "version": version,
                },
                network={"client": {"ip": host, "port": port}},
                duration=process_time,
            )
        return response
