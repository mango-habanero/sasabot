"""Entity registry - import all entities here for Alembic discovery."""

from .base import Base, IDMixin, TimestampMixin
from .booking import Booking
from .business import (
    Business,
    Configuration,
    Location,
    Promotion,
    Service,
    ServiceCategory,
)
from .conversation_session import ConversationSession
from .message import Message

# Export for convenience
__all__ = [
    "Base",
    "Booking",
    "Business",
    "Configuration",
    "ConversationSession",
    "IDMixin",
    "Location",
    "Message",
    "Promotion",
    "Service",
    "ServiceCategory",
    "TimestampMixin",
]
