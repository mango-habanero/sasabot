"""WhatsApp Cloud API client for sending messages."""

import httpx

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


class WhatsAppClient:
    """Client for WhatsApp Cloud API."""

    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.META_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        self.timeout = 30.0

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

    async def _send_request(
        self, payload: OutboundMessageRequest
    ) -> WhatsAppAPIResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload.model_dump(exclude_none=True),
                timeout=self.timeout,
            )

            # Raise for 4xx/5xx status codes
            response.raise_for_status()

            return WhatsAppAPIResponse(**response.json())
