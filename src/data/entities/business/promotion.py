"""Business promotion entity for promotional campaigns."""

from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Column, Date, Enum, Numeric, Text
from sqlmodel import Field

from src.data.entities.base import Base, IDMixin, TimestampMixin
from src.data.enums.business.promotion import PromotionStatus, PromotionType


class Promotion(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "promotions"

    business_id: int = Field(
        foreign_key="businesses.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    name: str = Field(max_length=255, nullable=False)
    description: str = Field(sa_column=Column(Text, nullable=False))
    promotion_type: PromotionType = Field(
        sa_column=Column(Enum(PromotionType), nullable=False)
    )
    discount_value: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    start_date: date | None = Field(default=None, sa_column=Column(Date))
    end_date: date | None = Field(default=None, sa_column=Column(Date))
    recurrence_rule: dict | None = Field(default=None, sa_column=Column(JSON))
    applicable_service_ids: list = Field(default_factory=list, sa_column=Column(JSON))
    status: PromotionStatus = Field(
        sa_column=Column(Enum(PromotionStatus)), default=PromotionStatus.ACTIVE
    )
    max_redemptions: int | None = Field(default=None, gt=0)
    current_redemptions: int = Field(default=0, nullable=False)
