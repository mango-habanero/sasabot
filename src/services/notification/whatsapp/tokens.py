from datetime import UTC, datetime, timedelta
from typing import Any, Optional, Type

import httpx

from src.common.interfaces import TokenProvider
from src.configuration import app_logger, settings
from src.data.dtos.responses import TokenDebugResponse
from src.data.dtos.requests import TokenDebugRequest, TokenExchangeRequest
from src.exceptions import TokenRefreshException


class MetaTokenManager(TokenProvider):
    def __init__(self) -> None:
        self._current_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._refresh_lock: bool = False
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)
        self._token_loaded: bool = False

    async def get_valid_token(self) -> str:
        if not self._token_loaded:
            await self._load_initial_token()

        if self._current_token and self._is_token_valid():
            return self._current_token

        token = await self._refresh_token()
        if token is None:
            raise TokenRefreshException("Failed to obtain WhatsApp token.")
        return token

    async def invalidate_token(self) -> None:
        self._current_token = None
        self._token_expires_at = None
        self._token_loaded = False
        app_logger.info("Token invalidated, will refresh on next request")

    def _is_token_valid(self) -> bool:
        if not self._current_token or not self._token_expires_at:
            return False
        buffer_time = timedelta(days=5)
        return datetime.now(UTC) < (self._token_expires_at - buffer_time)

    async def _load_initial_token(self) -> None:
        if self._token_loaded:
            return

        self._current_token = settings.META_SYSTEM_USER_TOKEN

        try:
            expiry_info = await self._get_token_expiry(self._current_token)
            self._token_expires_at = expiry_info
            self._token_loaded = True

            app_logger.info(
                "System user token loaded",
                expires_at=self._token_expires_at.isoformat()
                if self._token_expires_at
                else "unknown",
            )
        except Exception as e:
            app_logger.warning(
                "Could not fetch token expiry, using default 60-day window",
                error=str(e),
            )
            self._token_expires_at = datetime.now(UTC) + timedelta(days=60)
            self._token_loaded = True

    async def _get_token_expiry(self, token: str) -> datetime:
        request = TokenDebugRequest(
            input_token=token,
            access_token=f"{settings.META_APP_ID}|{settings.META_APP_SECRET}",
        )

        response = await self._client.get(
            f"https://graph.facebook.com/{settings.META_API_VERSION}/debug_token",
            params=request.model_dump(),
        )
        response.raise_for_status()

        debug_response = TokenDebugResponse(**response.json())

        if not debug_response.data.is_valid:
            raise TokenRefreshException("Token is not valid according to debug_token")

        expires_at_timestamp = debug_response.data.expires_at
        if expires_at_timestamp == 0:
            return datetime.now(UTC) + timedelta(days=60)

        return datetime.fromtimestamp(expires_at_timestamp, tz=UTC)

    async def _refresh_token(self) -> str:
        import asyncio

        if self._refresh_lock:
            await asyncio.sleep(0.5)
            if self._current_token and self._is_token_valid():
                return self._current_token

        self._refresh_lock = True
        try:
            app_logger.info("Exchanging system user token for new token")

            request = TokenExchangeRequest(
                client_id=settings.META_APP_ID,
                client_secret=settings.META_APP_SECRET,
                fb_exchange_token=self._current_token,
            )

            response = await self._client.get(
                f"https://graph.facebook.com/{settings.META_API_VERSION}/oauth/access_token",
                params=request.model_dump(),
            )
            response.raise_for_status()
            response_data = response.json()

            new_token = response_data.get("access_token")
            expires_in = int(response_data.get("expires_in", 5184000))

            if not isinstance(new_token, str):
                raise TokenRefreshException(
                    "No access token returned from Meta API", details=response_data
                )

            self._current_token = new_token
            self._token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

            app_logger.info(
                "System user token exchanged successfully",
                expires_in_days=expires_in // 86400,
                expires_at=self._token_expires_at.isoformat(),
            )

            return new_token
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            app_logger.error(
                "Token exchange failed",
                status_code=e.response.status_code if e.response else None,
                error=error_message,
            )
            raise TokenRefreshException(
                f"Failed to exchange system user token: {error_message}"
            ) from e
        except Exception as e:
            app_logger.error("Unexpected token exchange error", error=str(e))
            raise TokenRefreshException(
                f"Unexpected error during token exchange: {str(e)}"
            ) from e
        finally:
            self._refresh_lock = False

    async def __aenter__(self) -> "MetaTokenManager":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        await self._client.aclose()
