"""Message entity for audit trail and deduplication."""

from datetime import datetime

from sqlalchemy import TEXT, Column, Enum
from sqlmodel import Field

from src.data.entities import IDMixin
from src.data.entities.base import Base, TimestampMixin
from src.data.enums import MessageDirection, MessageStatus, MessageType


class Message(Base, IDMixin, TimestampMixin, table=True):
    """
    Represents a message entity used to store and manage details of messages
    exchanged via WhatsApp.

    Supports tracking message content, direction,
    status, and associated customer details.

    :ivar id: Unique identifier for a message, used for deduplication.
    :ivar customer_phone: Phone number of the customer involved in the
                          conversation.
    :ivar customer_name: Name of the customer; can be None if not provided.
    :ivar direction: Direction of the message, either inbound or outbound.
    :ivar external_id: External identifier for the message, used for tracking
    :ivar message_type: Type of the message, such as text, interactive,
                        button, or list.
    :ivar content: Body of the message or parsed data from an interactive
                   response.
    :ivar status: The current status of the message, relevant for outbound
                  messages; can be "sent", "delivered", "read", or "failed".
                  Maybe None if status tracking is not applicable.
    :ivar whatsapp_timestamp: Timestamp received from the WhatsApp webhook
                              service, stored in UTC format.
    """

    __tablename__ = "messages"

    customer_phone: str = Field(index=True, max_length=20)
    customer_name: str | None = Field(default=None, max_length=255)
    direction: MessageDirection = Field(sa_column=Column(Enum(MessageDirection)))
    external_id: str | None = Field(default=None, max_length=255, unique=True)
    message_type: MessageType = Field(
        sa_column=Column(Enum(MessageType), nullable=False)
    )
    content: str = Field(sa_column=Column(TEXT()))
    status: MessageStatus | None = Field(
        default=None, sa_column=Column(Enum(MessageStatus))
    )
    whatsapp_timestamp: datetime
