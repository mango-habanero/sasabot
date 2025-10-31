"""Entity registry - import all entities here for Alembic discovery."""

from .base import Base, IDMixin, TimestampMixin
from .booking import Booking
from .conversation_session import ConversationSession
from .message import Message

# Export for convenience
__all__ = [
    "Base",
    "Booking",
    "ConversationSession",
    "IDMixin",
    "Message",
    "TimestampMixin",
]
