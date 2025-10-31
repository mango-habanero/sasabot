"""Service for processing WhatsApp webhooks."""

from datetime import datetime, timezone

from sqlmodel import Session

from src.configuration import app_logger
from src.data.dtos import WebhookPayload
from src.data.entities.message import Message
from src.data.enums import MessageDirection
from src.data.repositories import MessageRepository
from src.data.repositories.conversation_session import ConversationSessionRepository
from src.services.conversation.service import ConversationService
from src.services.notification.whatsapp.client import WhatsAppClient


class WebhookService:
    """Service for processing WhatsApp webhooks."""

    def __init__(self, session: Session):
        self.session = session
        self.message_repo = MessageRepository(session)
        self.session_repo = ConversationSessionRepository(session)
        self.whatsapp_client = WhatsAppClient()

        # Initialize conversation service
        self.conversation_service = ConversationService(
            session_repository=self.session_repo,
            message_repository=self.message_repo,
            whatsapp_client=self.whatsapp_client,
        )

    async def process_webhook(self, payload: WebhookPayload) -> int:
        """
        Process incoming WhatsApp webhook.

        Saves inbound messages and delegates to ConversationService for response.

        :param payload: Webhook payload from WhatsApp
        :type payload: WebhookPayload
        :return: Number of new messages processed
        :rtype: int
        """
        messages = payload.extract_messages()
        contacts = payload.extract_contacts()

        # build contact map for a quick lookup
        contact_map = {
            contact.wa_id: contact.profile.get("name") for contact in contacts
        }

        processed_count = 0

        for webhook_msg in messages:
            # convert WhatsApp timestamp (unix seconds) to datetime
            whatsapp_ts = datetime.fromtimestamp(
                int(webhook_msg.timestamp), tz=timezone.utc
            )

            # create message entity
            message = Message(
                external_id=webhook_msg.id,
                customer_phone=webhook_msg.sender_phone,
                customer_name=contact_map.get(webhook_msg.sender_phone),
                direction=MessageDirection.INBOUND,
                message_type=webhook_msg.type,
                content=webhook_msg.content,
                status=None,  # Inbound messages don't have status
                whatsapp_timestamp=whatsapp_ts,
            )

            saved = self.message_repo.save(message)
            if saved:
                processed_count += 1
                app_logger.info(
                    "Webhook message processed",
                    message_id=saved.id,
                    customer_phone=saved.customer_phone,
                    message_type=saved.message_type,
                )

                # delegate to ConversationService to handle message and respond
                try:
                    await self.conversation_service.handle_message(
                        phone_number=webhook_msg.sender_phone,
                        message_content=webhook_msg.content,
                        customer_name=contact_map.get(webhook_msg.sender_phone),
                    )
                except Exception as e:
                    app_logger.error(
                        "Failed to handle message in conversation service",
                        message_id=saved.id,
                        customer_phone=saved.customer_phone,
                        error=str(e),
                    )
                    # continue processing other messages even if one fails

        app_logger.info(
            "Webhook processing complete",
            total_messages=len(messages),
            new_messages=processed_count,
            duplicates=len(messages) - processed_count,
        )

        return processed_count
