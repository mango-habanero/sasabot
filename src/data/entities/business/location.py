"""Business location entity for multi-location support."""

from sqlalchemy import JSON, TEXT, Column, Enum, UniqueConstraint
from sqlmodel import Field

from src.data.entities.base import Base, IDMixin, TimestampMixin
from src.data.enums.business.location import LocationStatus


class Location(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("business_id", "name", name="uq_location_name"),)

    business_id: int = Field(
        foreign_key="businesses.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    name: str = Field(max_length=255, nullable=False)
    address: str = Field(sa_column=Column(TEXT(), nullable=False))
    is_primary: bool = Field(default=False, nullable=False)
    operating_hours: dict = Field(sa_column=Column(JSON, nullable=False))
    status: LocationStatus = Field(
        sa_column=Column(Enum(LocationStatus)), default=LocationStatus.ACTIVE
    )
