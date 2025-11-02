"""Business-related enumerations."""

from enum import Enum


class BusinessStatus(Enum):
    """Business and location status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"
