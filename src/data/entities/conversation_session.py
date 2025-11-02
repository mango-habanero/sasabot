"""Conversation session entity for managing chat state."""

from typing import Any

from sqlalchemy import JSON, Column, Enum
from sqlmodel import Field

from src.data.entities.base import Base, IDMixin, TimestampMixin
from src.data.enums.conversation import ConversationState
from src.utilities import normalize_phone_number


class ConversationSession(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "conversation_sessions"

    business_id: int = Field(
        foreign_key="businesses.id",
        nullable=False,
        index=True,
        ondelete="RESTRICT",
    )
    context: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    phone_number: str = Field(index=True, unique=True, max_length=20)
    state: ConversationState = Field(
        sa_column=Column(Enum(ConversationState)), default=ConversationState.IDLE
    )

    def __init__(self, **data):
        phone_number = data.get("phone_number")
        if phone_number:
            data["phone_number"] = normalize_phone_number(phone_number)
        super().__init__(**data)
