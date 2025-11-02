"""Service for processing WhatsApp webhooks."""

from datetime import datetime, timezone

from sqlmodel import Session

from src.configuration import app_logger
from src.data.dtos.requests import WebhookPayload
from src.data.entities import Message
from src.data.enums import MessageDirection
from src.data.enums.business import BusinessStatus
from src.data.repositories.business import BusinessRepository
from src.data.repositories.conversation_session import ConversationSessionRepository
from src.data.repositories.message import MessageRepository
from src.services.conversation.service import ConversationService
from src.services.notification.whatsapp.client import WhatsAppClient


class WebhookService:
    def __init__(self, session: Session):
        self.session = session
        self.message_repo = MessageRepository(session)
        self.session_repo = ConversationSessionRepository(session)
        self.business_repo = BusinessRepository(session)
        self.whatsapp_client = WhatsAppClient()

        self.conversation_service = ConversationService(
            session_repository=self.session_repo,
            message_repository=self.message_repo,
            whatsapp_client=self.whatsapp_client,
        )

    async def process_webhook(self, payload: WebhookPayload) -> int:
        phone_number_id = payload.extract_phone_number_id()
        if not phone_number_id:
            app_logger.warning("Webhook received without phone_number_id")
            return 0

        business = self.business_repo.get_by_whatsapp_number_id(phone_number_id)
        if not business:
            app_logger.warning(
                "Business not found for phone_number_id, skipping webhook",
                phone_number_id=phone_number_id,
            )
            return 0

        if business.status != BusinessStatus.ACTIVE:
            app_logger.warning(
                "Business is not active, skipping webhook",
                business_id=business.id,
                business_status=business.status.value,
                phone_number_id=phone_number_id,
            )
            return 0

        app_logger.info(
            "Processing webhook for business",
            business_id=business.id,
            business_name=business.name,
            phone_number_id=phone_number_id,
        )

        messages = payload.extract_messages()
        contacts = payload.extract_contacts()

        contact_map = {
            contact.wa_id: contact.profile.get("name") for contact in contacts
        }

        processed_count = 0

        for webhook_msg in messages:
            whatsapp_ts = datetime.fromtimestamp(
                int(webhook_msg.timestamp), tz=timezone.utc
            )

            message = Message(
                external_id=webhook_msg.id,
                customer_phone=webhook_msg.sender_phone,
                customer_name=contact_map.get(webhook_msg.sender_phone),
                direction=MessageDirection.INBOUND,
                message_type=webhook_msg.type,
                content=webhook_msg.content,
                status=None,
                whatsapp_timestamp=whatsapp_ts,
            )

            saved = self.message_repo.save(message)
            if not saved:
                app_logger.warning(
                    "Failed to save message (likely duplicate)",
                    external_id=webhook_msg.id,
                    customer_phone=webhook_msg.sender_phone,
                )
                continue

            processed_count += 1
            app_logger.info(
                "Webhook message saved",
                message_id=saved.id,
                customer_phone=saved.customer_phone,
                message_type=saved.message_type,
            )

            try:
                await self.conversation_service.handle_message(
                    phone_number=webhook_msg.sender_phone,
                    message_content=webhook_msg.content,
                    business_id=business.id,
                    customer_name=contact_map.get(webhook_msg.sender_phone),
                )
            except Exception as e:
                app_logger.error(
                    "Failed to handle message in conversation service",
                    message_id=saved.id,
                    customer_phone=saved.customer_phone,
                    business_id=business.id,
                    error=str(e),
                    exc_info=True,
                )

        app_logger.info(
            "Webhook processing complete",
            business_id=business.id,
            total_messages=len(messages),
            processed_messages=processed_count,
            skipped_messages=len(messages) - processed_count,
        )

        return processed_count
