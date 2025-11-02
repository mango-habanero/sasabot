"""Category-related enumerations."""

from enum import Enum


class CategoryStatus(Enum):
    """Service category status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
