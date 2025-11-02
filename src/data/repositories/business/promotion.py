"""Repository for Promotion entity operations."""

from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from src.configuration import app_logger
from src.data.entities.business import Promotion
from src.data.enums.business import PromotionStatus


class PromotionRepository:
    """Repository for Promotion entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        name: str,
        description: str,
        promotion_type: str,
        discount_value: float,
        start_date: date | None = None,
        end_date: date | None = None,
        recurrence_rule: dict | None = None,
        applicable_service_ids: list | None = None,
        status: PromotionStatus = PromotionStatus.ACTIVE,
        max_redemptions: int | None = None,
    ) -> Promotion | None:
        try:
            promotion = Promotion(
                business_id=business_id,
                name=name,
                description=description,
                promotion_type=promotion_type,
                discount_value=discount_value,
                start_date=start_date,
                end_date=end_date,
                recurrence_rule=recurrence_rule,
                applicable_service_ids=applicable_service_ids or [],
                status=status,
                max_redemptions=max_redemptions,
                current_redemptions=0,
            )

            self.session.add(promotion)
            self.session.commit()
            self.session.refresh(promotion)

            app_logger.info(
                "Promotion created",
                promotion_id=promotion.id,
                business_id=business_id,
                name=name,
            )
            return promotion

        except IntegrityError as e:
            self.session.rollback()
            app_logger.warning(
                "Promotion creation failed - FK violation",
                business_id=business_id,
                name=name,
                error=str(e),
            )
            return None

    def get_by_id(
        self, promotion_id: int, include_deleted: bool = False
    ) -> Promotion | None:
        statement = select(Promotion).where(Promotion.id == promotion_id)

        if not include_deleted:
            statement = statement.where(Promotion.status != PromotionStatus.DELETED)

        return self.session.exec(statement).first()

    def get_active_by_business_id(self, business_id: int) -> list[Promotion]:
        today = date.today()

        statement = (
            select(Promotion)
            .where(Promotion.business_id == business_id)
            .where(Promotion.status == PromotionStatus.ACTIVE)
            .where(
                (col(Promotion.start_date).is_(None)) | (Promotion.start_date <= today)
            )
            .where((col(Promotion.end_date).is_(None)) | (Promotion.end_date >= today))
        )

        return list(self.session.exec(statement).all())

    def soft_delete(self, promotion_id: int) -> bool:
        promotion = self.session.get(Promotion, promotion_id)
        if not promotion:
            app_logger.warning(
                "Promotion not found for soft delete",
                promotion_id=promotion_id,
            )
            return False

        promotion.status = PromotionStatus.DELETED
        promotion.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Promotion soft deleted",
            promotion_id=promotion_id,
            business_id=promotion.business_id,
            name=promotion.name,
        )
        return True
