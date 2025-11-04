"""Repository for ServiceCategory entity operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from src.configuration import app_logger
from src.data.entities.business import ServiceCategory
from src.data.enums.business import CategoryStatus


class ServiceCategoryRepository:
    """Repository for ServiceCategory entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        name: str,
        description: str | None = None,
        display_order: int = 0,
        status: CategoryStatus = CategoryStatus.ACTIVE,
    ) -> ServiceCategory | None:
        try:
            category = ServiceCategory(
                business_id=business_id,
                name=name,
                description=description,
                display_order=display_order,
                status=status,
            )

            self.session.add(category)
            self.session.commit()
            self.session.refresh(category)

            app_logger.info(
                "Service category created",
                category_id=category.id,
                business_id=business_id,
                name=name,
            )
            return category

        except IntegrityError as e:
            self.session.rollback()
            app_logger.warning(
                "Service category creation failed - duplicate name or FK violation",
                business_id=business_id,
                name=name,
                error=str(e),
            )
            return None

    def get_by_id(
        self, category_id: int, include_deleted: bool = False
    ) -> ServiceCategory | None:
        statement = select(ServiceCategory).where(ServiceCategory.id == category_id)

        if not include_deleted:
            statement = statement.where(
                ServiceCategory.status != CategoryStatus.DELETED
            )

        return self.session.exec(statement).first()

    def get_by_business_id(
        self, business_id: int, include_deleted: bool = False
    ) -> list[ServiceCategory]:
        statement = select(ServiceCategory).where(
            ServiceCategory.business_id == business_id
        )

        if not include_deleted:
            statement = statement.where(
                ServiceCategory.status != CategoryStatus.DELETED
            )

        statement = statement.order_by(
            col(ServiceCategory.display_order), ServiceCategory.name
        )

        return list(self.session.exec(statement).all())

    def soft_delete(self, category_id: int) -> bool:
        category = self.session.get(ServiceCategory, category_id)
        if not category:
            app_logger.warning(
                "Service category not found for soft delete",
                category_id=category_id,
            )
            return False

        category.status = CategoryStatus.DELETED
        category.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Service category soft deleted",
            category_id=category_id,
            business_id=category.business_id,
            name=category.name,
        )
        return True
