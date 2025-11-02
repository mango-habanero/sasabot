"""Pricing service for business calculations."""

from decimal import ROUND_HALF_UP, Decimal

from src.configuration import app_logger
from src.data.entities import Promotion
from src.data.repositories import ConfigurationRepository
from src.exceptions import ResourceNotFoundError


def calculate_balance(service_price: Decimal, deposit_paid: Decimal) -> Decimal:
    balance = service_price - deposit_paid
    return balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_discount(
    service_price: Decimal, discount_value: Decimal, discount_type: str
) -> Decimal:
    if discount_type == "percentage_discount":
        percentage = discount_value / Decimal("100")
        discount = service_price * percentage
    elif discount_type == "fixed_amount":
        discount = discount_value
    else:
        app_logger.warning(
            "Unknown discount type, defaulting to 0",
            discount_type=discount_type,
        )
        discount = Decimal("0")

    discount = min(discount, service_price)
    return discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_price_display(price: Decimal) -> str:
    return f"KES {price:,.2f}"


class PricingService:
    def __init__(self, config_repository: ConfigurationRepository):
        self.config_repo = config_repository

    def calculate_deposit(self, service_price: Decimal, business_id: int) -> Decimal:
        config = self.config_repo.get_by_business_id(business_id)
        if not config:
            raise ResourceNotFoundError("configuration", business_id=business_id)

        percentage = Decimal(str(config.deposit_percentage)) / Decimal("100")
        deposit = service_price * percentage
        deposit = deposit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        app_logger.debug(
            "Deposit calculated",
            business_id=business_id,
            service_price=str(service_price),
            deposit_percentage=config.deposit_percentage,
            deposit=str(deposit),
        )

        return deposit

    def calculate_with_promotion(
        self,
        service_price: Decimal,
        business_id: int,
        promotion: Promotion | None = None,
    ) -> dict:
        config = self.config_repo.get_by_business_id(business_id)
        if not config:
            raise ResourceNotFoundError("configuration", business_id=business_id)

        discount_amount = Decimal("0")
        promotion_name = None

        if promotion:
            discount_amount = calculate_discount(
                service_price=service_price,
                discount_value=Decimal(str(promotion.discount_value)),
                discount_type=promotion.promotion_type.value,
            )
            promotion_name = promotion.name

            app_logger.debug(
                "Promotion applied",
                business_id=business_id,
                promotion_id=promotion.id,
                promotion_name=promotion_name,
                discount_amount=str(discount_amount),
            )

        final_price = service_price - discount_amount
        deposit_amount = self.calculate_deposit(final_price, business_id)
        balance_amount = calculate_balance(final_price, deposit_amount)

        result = {
            "original_price": service_price,
            "discount_amount": discount_amount,
            "final_price": final_price,
            "deposit_amount": deposit_amount,
            "balance_amount": balance_amount,
            "promotion_applied": promotion_name,
            "deposit_percentage": config.deposit_percentage,
        }

        app_logger.debug(
            "Pricing calculated with promotion",
            business_id=business_id,
            original_price=str(service_price),
            final_price=str(final_price),
            discount=str(discount_amount),
            deposit=str(deposit_amount),
            has_promotion=bool(promotion),
        )

        return result

    def format_deposit_display(self, service_price: Decimal, business_id: int) -> str:
        deposit = self.calculate_deposit(service_price, business_id)
        config = self.config_repo.get_by_business_id(business_id)

        return (
            f"{format_price_display(deposit)} "
            f"({config.deposit_percentage:.0f}% deposit)"
        )
