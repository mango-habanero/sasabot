"""Enums for conversation management."""

from enum import Enum


class ConversationState(Enum):
    """Conversation state enumeration."""

    # Base states
    IDLE = "idle"  # Waiting for user input
    PROCESSING_INTENT = "processing"  # LLM analyzing message

    # Booking sub-flow
    BOOKING_SELECT_SERVICE = "booking_service"
    BOOKING_SELECT_DATETIME = "booking_datetime"
    BOOKING_CONFIRM = "booking_confirm"

    # Payment sub-flow
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_PENDING = "payment_pending"

    # Feedback sub-flow
    FEEDBACK_RATING = "feedback_rating"
    FEEDBACK_COMMENT = "feedback_comment"
