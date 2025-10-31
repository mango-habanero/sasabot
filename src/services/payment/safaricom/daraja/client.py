"""Daraja API client for M-Pesa STK Push integration."""

import base64
from datetime import datetime, timezone

import httpx

from src.configuration import app_logger, settings
from src.data.dtos.requests.daraja import STKPushRequest
from src.data.dtos.responses.daraja import AccessTokenResponse, STKPushResponse


class DarajaClient:
    """Client for Safaricom Daraja M-Pesa API."""

    def __init__(self):
        """Initialize Daraja client with settings."""
        self.base_url = settings.DARAJA_URL
        self.consumer_key = settings.DARAJA_CONSUMER_KEY
        self.consumer_secret = settings.DARAJA_CONSUMER_SECRET
        self.shortcode = settings.DARAJA_BUSINESS_SHORTCODE
        self.passkey = settings.DARAJA_PASSKEY

    async def get_access_token(self) -> str:
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"

        # Create Basic Auth header
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers = {"Authorization": f"Basic {auth_b64}"}

        app_logger.debug("Requesting Daraja access token")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            token_response = AccessTokenResponse(**response.json())

            app_logger.info(
                "Access token obtained",
                expires_in=token_response.expires_in,
            )

            return token_response.access_token

    def generate_password(self, timestamp: str) -> str:
        raw_password = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = raw_password.encode("utf-8")
        return base64.b64encode(password_bytes).decode("utf-8")

    def _get_phone_and_parties(self, customer_phone: str) -> tuple[str, str, str]:
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
        access_token = await self.get_access_token()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        password = self.generate_password(timestamp)

        phone_number, party_a, party_b = self._get_phone_and_parties(customer_phone)
        amount = "1" if settings.ENVIRONMENT == "development" else str(amount)

        # Build request
        stk_request = STKPushRequest(
            BusinessShortCode=self.shortcode,
            Password=password,
            Timestamp=timestamp,
            Amount=str(amount),
            PartyA=phone_number,
            PartyB=party_b,
            PhoneNumber=phone_number,
            CallBackURL=callback_url,
            AccountReference=account_reference,
            TransactionDesc=transaction_desc,
        )
        app_logger.info(
            "STK Push request created",
            amount=amount,
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
            amount=amount,
            account_reference=account_reference,
            phone_number=phone_number,
            environment=settings.ENVIRONMENT,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
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
