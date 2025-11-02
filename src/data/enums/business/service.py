"""Service-related enumerations."""

from enum import Enum


class ServiceStatus(Enum):
    """Service availability status enumeration."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    SEASONAL = "seasonal"
    DELETED = "deleted"
