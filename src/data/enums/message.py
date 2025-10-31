from enum import Enum


class MessageDirection(Enum):
    """Message directions."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(Enum):
    """Message statuses."""

    DELIVERED = "delivered"
    FAILED = "failed"
    PENDING = "pending"
    READ = "read"
    SENT = "sent"


class MessageType(Enum):
    """Message types."""

    BUTTON = "button"
    INTERACTIVE = "interactive"
    LIST = "list"
    TEXT = "text"
