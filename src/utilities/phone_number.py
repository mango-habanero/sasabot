"""Utilities for working with phone numbers."""

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import NumberParseException


def normalize_phone_number(phone: str, fallback_region: str = "KE") -> str:
    if not phone:
        raise ValueError("Phone number cannot be empty")

    phone = phone.strip().replace(" ", "").replace("-", "")

    try:
        parsed = phonenumbers.parse(phone, None)
    except NumberParseException:
        try:
            parsed = phonenumbers.parse(phone, fallback_region)
        except NumberParseException as e:
            raise ValueError(f"Invalid phone number format: {phone}") from e

    if not phonenumbers.is_possible_number(parsed):
        raise ValueError(f"Phone number not possible: {phone}")

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError(f"Invalid phone number: {phone}")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def is_safaricom_number(phone_number: str) -> bool:
    try:
        parsed = phonenumbers.parse(phone_number, "KE")
        carrier_name = carrier.name_for_number(parsed, "en")
        return carrier_name.lower() == "safaricom"

    except Exception:
        return False
