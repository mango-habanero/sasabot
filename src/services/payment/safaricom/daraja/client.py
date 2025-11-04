import base64
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Optional

import httpx

from src.common.interfaces import TokenProvider
from src.configuration import app_logger, settings
from src.data.dtos.requests.daraja import STKPushRequest
from src.data.dtos.responses.daraja import STKPushResponse
from src.exceptions import ExternalServiceException, TokenRefreshException

from .tokens import DarajaTokenManager


class DarajaClient:
    """Client for Safaricom Daraja M-Pesa API with automatic token management."""

    def __init__(self, token_provider: Optional[TokenProvider] = None):
        self.base_url = settings.DARAJA_URL
        self.shortcode = settings.DARAJA_BUSINESS_SHORTCODE
        self.passkey = settings.DARAJA_PASSKEY
        self.token_provider = token_provider or DarajaTokenManager()
        self._client = httpx.AsyncClient(timeout=30.0)

    def generate_password(self, timestamp: str) -> str:
        """Generate security credential password for Daraja API."""
        raw_password = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = raw_password.encode("utf-8")
        return base64.b64encode(password_bytes).decode("utf-8")

    def _get_phone_and_parties(self, customer_phone: str) -> tuple[str, str, str]:
        """Get appropriate phone numbers and parties based on the environment."""
        if settings.ENVIRONMENT == "development":
            # Use sandbox test numbers
            phone_number = settings.DARAJA_SANDBOX_PHONE_NUMBER
            party_a = settings.DARAJA_SANDBOX_PARTY_A
            party_b = settings.DARAJA_SANDBOX_PARTY_B

            app_logger.debug(
                "Using sandbox credentials",
                sandbox_phone=phone_number,
            )
        else:
            # Use real customer phone in production
            phone_number = customer_phone
            party_a = customer_phone
            party_b = self.shortcode

            app_logger.debug(
                "Using production credentials",
                customer_phone=customer_phone,
            )

        return phone_number, party_a, party_b

    async def initiate_stk_push(
        self,
        customer_phone: str,
        amount: int,
        account_reference: str,
        transaction_desc: str,
        callback_url: str,
    ) -> STKPushResponse:
        try:
            access_token = await self.token_provider.get_valid_token()
        except TokenRefreshException as e:
            app_logger.error("Failed to get valid Daraja token", error=str(e))
            raise ExternalServiceException(
                "Payment service unavailable - unable to authenticate with payment provider"
            ) from e

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        password = self.generate_password(timestamp)

        phone_number, party_a, party_b = self._get_phone_and_parties(customer_phone)
        # Use KES 1 in sandbox for testing
        amount_str = "1" if settings.ENVIRONMENT == "development" else str(amount)

        # Build request
        stk_request = STKPushRequest(
            BusinessShortCode=self.shortcode,
            Password=password,
            Timestamp=timestamp,
            Amount=amount_str,
            PartyA=phone_number,
            PartyB=party_b,
            PhoneNumber=phone_number,
            CallBackURL=callback_url,
            AccountReference=account_reference,
            TransactionDesc=transaction_desc,
        )

        app_logger.info(
            "STK Push request created",
            amount=amount_str,
            account_reference=account_reference,
            phone_number=phone_number,
            environment=settings.ENVIRONMENT,
            data=stk_request.model_dump(by_alias=True),
        )

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        app_logger.info(
            "Initiating STK Push",
            amount=amount_str,
            account_reference=account_reference,
            phone_number=phone_number,
            environment=settings.ENVIRONMENT,
        )

        try:
            response = await self._client.post(
                url,
                headers=headers,
                json=stk_request.model_dump(by_alias=True),
                timeout=30.0,
            )

            # Handle 401 Unauthorized errors (token expired)
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                app_logger.warning(
                    "STK Push failed with 401, refreshing token and retrying"
                )
                await self.token_provider.invalidate_token()

                # get a new token and retry
                access_token = await self.token_provider.get_valid_token()
                headers["Authorization"] = f"Bearer {access_token}"

                response = await self._client.post(
                    url,
                    headers=headers,
                    json=stk_request.model_dump(by_alias=True),
                    timeout=30.0,
                )

            response.raise_for_status()
            stk_response = STKPushResponse(**response.json())

            app_logger.info(
                "STK Push initiated successfully",
                checkout_request_id=stk_response.checkout_request_id,
                response_code=stk_response.response_code,
                response_description=stk_response.response_description,
            )

            return stk_response

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            error_message = error_data.get("errorMessage", str(e))

            app_logger.error(
                "STK Push failed",
                status_code=e.response.status_code if e.response else None,
                error=error_message,
                request_data=stk_request.model_dump(by_alias=True),
            )

            # Handle specific Daraja error codes
            if e.response and e.response.status_code == 400:
                if (
                    "Invalid access token" in error_message
                    or "The access token is invalid" in error_message
                ):
                    await self.token_provider.invalidate_token()

            raise ExternalServiceException(
                f"Payment initiation failed: {error_message}"
            ) from e
        except Exception as e:
            app_logger.error(
                "Unexpected error in STK Push initiation",
                error=str(e),
                request_data=stk_request.model_dump(by_alias=True),
            )
            raise ExternalServiceException(
                "Payment service temporarily unavailable"
            ) from e

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
