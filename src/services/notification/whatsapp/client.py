"""WhatsApp Cloud API client for sending messages."""

from typing import Optional

import httpx

from src.common.interfaces import TokenProvider
from src.configuration import app_logger
from src.configuration.settings import settings
from src.data.dtos import (
    ButtonReply,
    DocumentMedia,
    Interactive,
    InteractiveAction,
    InteractiveBody,
    InteractiveFooter,
    InteractiveHeader,
    OutboundMessageRequest,
    TextMessage,
    WhatsAppAPIResponse,
)
from src.exceptions import ExternalServiceException

from .tokens import MetaTokenManager


class WhatsAppClient:
    """Client for WhatsApp Cloud API."""

    def __init__(self, token_provider: Optional[TokenProvider] = None):
        self.base_url = f"https://graph.facebook.com/{settings.META_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        self.timeout = 30.0
        self.token_provider = token_provider or MetaTokenManager()
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def send_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[tuple[str, str]],
        header_text: str | None = None,
        footer_text: str | None = None,
    ) -> WhatsAppAPIResponse:
        if len(buttons) > 3:
            raise ValueError("WhatsApp supports maximum 3 buttons")

        if len(buttons) < 1:
            raise ValueError("At least 1 button required")

        button_replies = [
            ButtonReply(
                type="reply",
                reply={"id": btn_id, "title": btn_title[:20]},  # Max 20 chars for title
            )
            for btn_id, btn_title in buttons
        ]

        interactive = Interactive(
            type="button",
            body=InteractiveBody(text=body_text),
            action=InteractiveAction(buttons=button_replies),
        )

        if header_text:
            interactive.header = InteractiveHeader(type="text", text=header_text)

        if footer_text:
            interactive.footer = InteractiveFooter(text=footer_text)

        payload = OutboundMessageRequest(
            to=to,
            type="interactive",
            interactive=interactive,
        )

        response = await self._send_request(payload)

        app_logger.info(
            "Button message sent",
            recipient=to,
            message_id=response.message_id,
            button_count=len(buttons),
        )

        return response

    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: str | None = None,
    ) -> WhatsAppAPIResponse:
        payload = OutboundMessageRequest(
            to=to,
            type="document",
            document=DocumentMedia(
                link=document_url,
                filename=filename,
                caption=caption,
            ),
        )

        response = await self._send_request(payload)

        app_logger.info(
            "Document sent",
            recipient=to,
            message_id=response.message_id,
            filename=filename,
        )

        return response

    async def send_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: list[dict],
        header_text: str | None = None,
        footer_text: str | None = None,
    ) -> WhatsAppAPIResponse:
        total_rows = sum(len(section.get("rows", [])) for section in sections)
        if len(sections) > 10:
            raise ValueError("WhatsApp supports maximum 10 sections")
        if total_rows > 10:
            raise ValueError(
                "WhatsApp supports maximum 10 total rows across all sections"
            )

        interactive = Interactive(
            type="list",
            body=InteractiveBody(text=body_text),
            action=InteractiveAction(
                button=button_text[:20],  # Max 20 chars
                sections=sections,
            ),
        )

        if header_text:
            interactive.header = InteractiveHeader(type="text", text=header_text)

        if footer_text:
            interactive.footer = InteractiveFooter(text=footer_text)

        payload = OutboundMessageRequest(
            to=to,
            type="interactive",
            interactive=interactive,
        )

        response = await self._send_request(payload)

        app_logger.info(
            "List message sent",
            recipient=to,
            message_id=response.message_id,
            section_count=len(sections),
            row_count=total_rows,
        )

        return response

    async def send_text(
        self,
        to: str,
        text: str,
        preview_url: bool = False,
    ) -> WhatsAppAPIResponse:
        payload = OutboundMessageRequest(
            to=to,
            type="text",
            text=TextMessage(body=text, preview_url=preview_url),
        )

        response = await self._send_request(payload)

        app_logger.info(
            "Text message sent",
            recipient=to,
            message_id=response.message_id,
        )

        return response

    async def _get_headers(self) -> dict:
        """Get headers with valid access token."""
        token = await self.token_provider.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _send_request(
        self, payload: OutboundMessageRequest
    ) -> WhatsAppAPIResponse:
        headers = await self._get_headers()

        try:
            response = await self._client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload.model_dump(exclude_none=True),
                timeout=self.timeout,
            )

            # Handle 401 Unauthorized errors for token refresh
            if response.status_code == 401:
                app_logger.warning(
                    "Received 401 Unauthorized, invalidating token and retrying"
                )

                # Invalidate current token and get new headers
                await self.token_provider.invalidate_token()
                headers = await self._get_headers()

                # Retry the request once with new token
                response = await self._client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload.model_dump(exclude_none=True),
                    timeout=self.timeout,
                )

            response.raise_for_status()
            return WhatsAppAPIResponse(**response.json())

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            error_message = error_data.get("error", {}).get("message", str(e))

            app_logger.error(
                "WhatsApp API request failed",
                status_code=e.response.status_code if e.response else None,
                error=error_message,
                payload=payload.model_dump(exclude_none=True),
            )

            # Handle permanent token errors
            if (
                e.response
                and e.response.status_code == 400
                and "Invalid OAuth access token" in error_message
            ):
                await self.token_provider.invalidate_token()

            raise ExternalServiceException(
                f"WhatsApp API error: {error_message}",
                details=error_data,
            ) from e
        except Exception as e:
            app_logger.error(
                "Unexpected error in WhatsApp API request",
                error=str(e),
                payload=payload.model_dump(exclude_none=True),
            )
            raise ExternalServiceException("Failed to send WhatsApp message") from e

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
