"""Business service category entity for service organization."""

from sqlalchemy import Column, Enum, Text, UniqueConstraint
from sqlmodel import Field

from src.data.entities.base import Base, IDMixin, TimestampMixin
from src.data.enums import CategoryStatus


class ServiceCategory(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "service_categories"
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_business_category_name"),
    )

    business_id: int = Field(
        foreign_key="businesses.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    name: str = Field(max_length=100, nullable=False)
    description: str | None = Field(default=None, sa_column=Column(Text))
    display_order: int = Field(default=0, nullable=False)
    status: CategoryStatus = Field(
        sa_column=Column(Enum(CategoryStatus)), default=CategoryStatus.ACTIVE
    )
