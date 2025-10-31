"""Enums for intent recognition."""

from enum import Enum


class IntentType(Enum):
    """User intent types for conversation routing."""

    GENERAL_INQUIRY = "general_inquiry"  # Questions about business, hours, location
    BOOK_APPOINTMENT = "book_appointment"  # Want to book a service
    PRICE_CHECK = "price_check"  # Asking about service prices
    PAYMENT_RELATED = "payment_related"  # Payment questions or issues
    FEEDBACK = "feedback"  # Want to provide feedback
    UNKNOWN = "unknown"  # Cannot determine intent
