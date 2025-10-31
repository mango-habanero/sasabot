"""Booking utility functions."""

import secrets
from datetime import datetime, timezone


def generate_booking_reference() -> str:
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")

    # Generate random 4-character suffix (uppercase letters and digits)
    suffix = "".join(
        secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(4)
    )

    return f"GLW-{date_part}-{suffix}"


def calculate_deposit(service_price: int) -> dict[str, int]:
    deposit = int(service_price * 0.3)
    balance = service_price - deposit

    return {
        "deposit_amount": deposit,
        "balance_amount": balance,
        "total_amount": service_price,
    }
