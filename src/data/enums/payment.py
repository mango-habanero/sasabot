from enum import Enum


class PaymentStatus(Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
