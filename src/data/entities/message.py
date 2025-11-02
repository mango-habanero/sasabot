"""Message entity for audit trail and deduplication."""

from datetime import datetime

from sqlalchemy import TEXT, Column, Enum
from sqlmodel import Field

from src.data.entities import IDMixin
from src.data.entities.base import Base, TimestampMixin
from src.data.enums import MessageDirection, MessageStatus, MessageType


class Message(Base, IDMixin, TimestampMixin, table=True):
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
