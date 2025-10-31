"""Message repository for database operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from src.configuration import app_logger
from src.data.entities.message import Message
from src.data.enums import MessageDirection, MessageStatus, MessageType


class MessageRepository:
    """Repository for Message entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, message: Message) -> Message | None:
        """
        Save a message to the database.

        Returns None if a message already exists (duplicate webhook).

        :param message: Message entity to save
        :return: the saved message or None if duplicate
        """
        try:
            self.session.add(message)
            self.session.commit()
            self.session.refresh(message)

            app_logger.info(
                "Message saved",
                message_id=message.id,
                customer_phone=message.customer_phone,
                direction=message.direction,
            )
            return message

        except IntegrityError:
            self.session.rollback()
            app_logger.warning(
                "Duplicate message ignored",
                message_id=message.id,
                customer_phone=message.customer_phone,
            )
            return None

    def get_by_id(self, message_id: str) -> Message | None:
        """
        Retrieve a message by its ID.

        :param message_id: WhatsApp message ID
        :return: Message entity or None if not found
        """
        return self.session.get(Message, message_id)

    def get_conversation_history(
        self,
        customer_phone: str,
        limit: int = 50,
    ) -> list[Message]:
        """
        Get conversation history for a customer, ordered by timestamp.

        :param customer_phone: Customer phone number
        :param limit: Maximum number of messages to retrieve
        :return: List of messages ordered by timestamp (oldest first)
        """
        statement = (
            select(Message)
            .where(Message.customer_phone == customer_phone)
            .order_by(col(Message.whatsapp_timestamp))
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def save_outbound(
        self,
        customer_phone: str,
        content: str,
        message_type: MessageType,
        whatsapp_message_id: str,
        customer_name: str | None = None,
    ) -> Message | None:
        """
        Saves an outbound message with given details.

        :param customer_phone: The phone number of the customer the message is being
            sent to.
        :type customer_phone: str
        :param content: The content of the outbound message.
        :type content: str
        :param message_type: The type of the message being sent (e.g., text, image).
        :type message_type: MessageType
        :param whatsapp_message_id: The ID of the message for tracking purposes in
            WhatsApp.
        :type whatsapp_message_id: str
        :param customer_name: (Optional) The name of the customer the message is being
            sent to, if available.
        :type customer_name: str | None
        :return: The saved `Message` object if the operation is successful; otherwise,
            returns `None`.
        :rtype: Message | None
        """
        message = Message(
            customer_phone=customer_phone,
            customer_name=customer_name,
            direction=MessageDirection.OUTBOUND,
            external_id=whatsapp_message_id,
            message_type=message_type,
            content=content,
            status=MessageStatus.PENDING,
            whatsapp_timestamp=datetime.now(timezone.utc),
        )

        return self.save(message)

    def update_status(self, message_id: str, status: str) -> bool:
        """
        Update message delivery status (for outbound messages).

        :param message_id: WhatsApp message ID
        :param status: New status ("sent", "delivered", "read", "failed")
        :return: True if updated, False if the message is not found
        """
        message = self.get_by_id(message_id)
        if not message:
            app_logger.warning(
                "Message not found for status update", message_id=message_id
            )
            return False

        message.status = MessageStatus[status.upper()]
        message.updated_at = datetime.now()
        self.session.commit()

        app_logger.info(
            "Message status updated",
            message_id=message_id,
            status=status,
        )
        return True
