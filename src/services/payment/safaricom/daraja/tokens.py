import asyncio
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Type

import httpx
from httpx import Response

from src.common.interfaces.token_provider import TokenProvider
from src.configuration import app_logger, settings
from src.data.dtos.responses.daraja import AccessTokenResponse
from src.exceptions import TokenRefreshException


class DarajaTokenManager(TokenProvider):
    def __init__(self) -> None:
        self._current_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._refresh_lock: bool = False
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)

    async def get_valid_token(self) -> str:
        """Return a valid token, refreshing if necessary."""
        if self._current_token and self._is_token_valid():
            return self._current_token

        token = await self._refresh_token()
        if token is None:
            raise TokenRefreshException("Failed to obtain Daraja token.")
        return token

    async def invalidate_token(self) -> None:
        """Invalidate the current token to force refresh on the next request."""
        self._current_token = None
        self._token_expires_at = None
        app_logger.info("Daraja token invalidated, will refresh on next request")

    def _is_token_valid(self) -> bool:
        """Check if the current token is valid based on expiration time."""
        if not self._current_token or not self._token_expires_at:
            return False

        buffer_time = timedelta(minutes=1)
        return datetime.now(timezone.utc) < (self._token_expires_at - buffer_time)

    async def _refresh_token(self) -> str:
        """Request a new token from the Daraja API."""
        if self._refresh_lock:
            await asyncio.sleep(0.5)
            if self._current_token and self._is_token_valid():
                return self._current_token

        self._refresh_lock = True
        try:
            app_logger.debug("Requesting Daraja access token")

            # create Basic Auth header
            auth_string = (
                f"{settings.DARAJA_CONSUMER_KEY}:{settings.DARAJA_CONSUMER_SECRET}"
            )
            auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

            headers = {"Authorization": f"Basic {auth_b64}"}
            url = (
                f"{settings.DARAJA_URL}/oauth/v1/generate?grant_type=client_credentials"
            )

            response: Response = await self._client.get(url, headers=headers)
            response.raise_for_status()

            token_response = AccessTokenResponse(**response.json())

            self._current_token = token_response.access_token
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=float(token_response.expires_in)
            )

            app_logger.info(
                "Daraja access token obtained",
                expires_in=token_response.expires_in,
                expires_at=self._token_expires_at.isoformat(),
            )

            return self._current_token

        except httpx.HTTPStatusError as e:
            error_data: dict[str, Any] = e.response.json() if e.response else {}
            error_message: str = error_data.get("error_description", str(e))
            app_logger.error(
                "Daraja token refresh failed",
                status_code=e.response.status_code if e.response else None,
                error=error_message,
            )
            raise TokenRefreshException(
                f"Failed to refresh Daraja token: {error_message}", details=error_data
            ) from e
        except Exception as e:
            app_logger.error("Unexpected Daraja token refresh error", error=str(e))
            raise TokenRefreshException(
                f"Unexpected error during Daraja token refresh: {str(e)}"
            ) from e
        finally:
            self._refresh_lock = False

    async def __aenter__(self) -> "DarajaTokenManager":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        await self._client.aclose()
