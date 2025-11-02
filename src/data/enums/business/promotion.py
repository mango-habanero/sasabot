"""Promotion-related enumerations."""

from enum import Enum


class PromotionStatus(Enum):
    """Promotion lifecycle status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class PromotionType(Enum):
    """Promotion calculation type enumeration."""

    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "bogo"  # Buy One Get One
    FREE_ADDON = "free_addon"
