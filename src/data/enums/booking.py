from enum import Enum


class BookingStatus(Enum):
    """Booking status enumeration."""

    PENDING = "pending"  # Awaiting payment
    CONFIRMED = "confirmed"  # Payment received
    CANCELLED = "cancelled"  # User or system cancelled
    COMPLETED = "completed"  # Service delivered
