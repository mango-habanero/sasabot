"""Base models and registry for database entities."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel

# Naming convention for constraints (enables clear error messages and migrations)
NAMING_CONVENTION: dict[str, Any] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(SQLModel):
    """Base class for all database models."""

    metadata = metadata


class IDMixin:
    """Provides auto-incrementing integer primary key."""

    __abstract__ = True

    id: Optional[int] = Field(default=None, primary_key=True, index=True)


class TimestampMixin:
    """Provides created_at and updated_at timestamp fields (stored as UTC)."""

    __abstract__ = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
