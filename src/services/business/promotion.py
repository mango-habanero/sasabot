"""Promotion service for discount calculation and validation."""

from datetime import date
from decimal import Decimal

from src.configuration import app_logger
from src.data.entities.business import Promotion
from src.data.repositories.business import PromotionRepository
from src.services.business import (
    PricingService,
    calculate_discount,
    format_price_display,
)


def applies_to_service(promotion: Promotion, service_id: int) -> bool:
    if not promotion.applicable_service_ids:
        return True

    return service_id in promotion.applicable_service_ids


def is_promotion_valid(promotion: Promotion, check_date: date) -> bool:
    if promotion.start_date and check_date < promotion.start_date:
        return False

    if promotion.end_date and check_date > promotion.end_date:
        return False

    if (
        promotion.max_redemptions is not None
        and promotion.current_redemptions >= promotion.max_redemptions
    ):
        return False

    return True


def is_recurrence_day(promotion: Promotion, check_date: date) -> bool:
    if not promotion.recurrence_rule:
        return True

    recurrence_type = promotion.recurrence_rule.get("type")

    if recurrence_type == "weekly":
        days = promotion.recurrence_rule.get("days", [])
        if not days:
            return True

        weekday_name = check_date.strftime("%A").lower()
        return weekday_name in days

    return True


def calculate_discounted_price(service_price: Decimal, promotion: Promotion) -> dict:
    discount_amount = calculate_discount(
        service_price=service_price,
        discount_value=Decimal(str(promotion.discount_value)),
        discount_type=promotion.promotion_type.value,
    )

    final_price = service_price - discount_amount

    return {
        "original_price": service_price,
        "discount_amount": discount_amount,
        "final_price": final_price,
        "promotion_id": promotion.id,
        "promotion_name": promotion.name,
    }


def get_promotion_summary(promotion: Promotion, service_price: Decimal) -> str:
    result = calculate_discounted_price(service_price, promotion)

    discount_display = format_price_display(result["discount_amount"])

    if promotion.promotion_type.value == "percentage_discount":
        return f"Save {discount_display} ({promotion.discount_value:.0f}% off) with {promotion.name}"
    elif promotion.promotion_type.value == "fixed_amount":
        return f"Save {discount_display} with {promotion.name}"
    else:
        return f"{promotion.name} applied"


def select_best_promotion(
    promotions: list[Promotion], service_price: Decimal
) -> Promotion | None:
    if not promotions:
        return None

    best_promotion = None
    max_discount = Decimal("0")

    for promotion in promotions:
        result = calculate_discounted_price(service_price, promotion)
        discount = result["discount_amount"]

        if discount > max_discount:
            max_discount = discount
            best_promotion = promotion

    if best_promotion:
        app_logger.debug(
            "Best promotion selected",
            promotion_id=best_promotion.id,
            promotion_name=best_promotion.name,
            discount_amount=str(max_discount),
        )

    return best_promotion


class PromotionService:
    def __init__(
        self,
        promotion_repository: PromotionRepository,
        pricing_service: PricingService,
    ):
        self.promotion_repo = promotion_repository
        self.pricing_service = pricing_service

    def get_applicable_promotions(
        self, business_id: int, service_id: int, check_date: date
    ) -> list[Promotion]:
        all_promotions = self.promotion_repo.get_active_by_business_id(business_id)

        applicable = [
            promo
            for promo in all_promotions
            if is_promotion_valid(promo, check_date)
            and applies_to_service(promo, service_id)
            and is_recurrence_day(promo, check_date)
        ]

        app_logger.debug(
            "Applicable promotions filtered",
            business_id=business_id,
            service_id=service_id,
            check_date=str(check_date),
            total_promotions=len(all_promotions),
            applicable_count=len(applicable),
        )

        return applicable
