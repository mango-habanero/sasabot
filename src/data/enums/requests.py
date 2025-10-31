"""Http request enumerations."""

from enum import Enum


class ResponseStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
