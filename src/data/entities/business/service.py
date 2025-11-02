"""Business service entity for service catalog."""

from decimal import Decimal

from sqlalchemy import TEXT, Column, Enum, Numeric, UniqueConstraint
from sqlmodel import Field

from src.data.entities.base import Base, IDMixin, TimestampMixin
from src.data.enums.business.service import ServiceStatus


class Service(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("business_id", "category_id", "name", name="uq_service_name"),
    )

    business_id: int = Field(
        foreign_key="businesses.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    category_id: int = Field(
        foreign_key="service_categories.id",
        nullable=False,
        index=True,
        ondelete="RESTRICT",
    )
    name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None, sa_column=Column(TEXT()))
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    duration_minutes: int = Field(nullable=False, gt=0)
    status: ServiceStatus = Field(
        sa_column=Column(Enum(ServiceStatus)), default=ServiceStatus.AVAILABLE
    )
    display_order: int = Field(default=0, nullable=False)
