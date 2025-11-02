"""Repository for Service entity operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.configuration import app_logger
from src.data.entities.business import Service
from src.data.enums.business import ServiceStatus


class ServiceRepository:
    """Repository for Service entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        category_id: int,
        name: str,
        price: float,
        duration_minutes: int,
        description: str | None = None,
        status: ServiceStatus = ServiceStatus.AVAILABLE,
        display_order: int = 0,
    ) -> Service | None:
        try:
            service = Service(
                business_id=business_id,
                category_id=category_id,
                name=name,
                price=price,
                duration_minutes=duration_minutes,
                description=description,
                status=status,
                display_order=display_order,
            )

            self.session.add(service)
            self.session.commit()
            self.session.refresh(service)

            app_logger.info(
                "Service created",
                service_id=service.id,
                business_id=business_id,
                category_id=category_id,
                name=name,
            )
            return service

        except IntegrityError as e:
            self.session.rollback()
            app_logger.warning(
                "Service creation failed - duplicate name or FK violation",
                business_id=business_id,
                category_id=category_id,
                name=name,
                error=str(e),
            )
            return None

    def get_by_id(
        self, service_id: int, include_deleted: bool = False
    ) -> Service | None:
        statement = select(Service).where(Service.id == service_id)

        if not include_deleted:
            statement = statement.where(Service.status != ServiceStatus.DELETED)

        return self.session.exec(statement).first()

    def get_by_business_id(
        self, business_id: int, include_deleted: bool = False
    ) -> list[Service]:
        statement = select(Service).where(Service.business_id == business_id)

        if not include_deleted:
            statement = statement.where(Service.status != ServiceStatus.DELETED)

        statement = statement.order_by(Service.display_order, Service.name)

        return list(self.session.exec(statement).all())

    def get_by_category_id(
        self, category_id: int, include_deleted: bool = False
    ) -> list[Service]:
        statement = select(Service).where(Service.category_id == category_id)

        if not include_deleted:
            statement = statement.where(Service.status != ServiceStatus.DELETED)

        statement = statement.order_by(Service.display_order, Service.name)

        return list(self.session.exec(statement).all())

    def soft_delete(self, service_id: int) -> bool:
        service = self.session.get(Service, service_id)
        if not service:
            app_logger.warning(
                "Service not found for soft delete",
                service_id=service_id,
            )
            return False

        service.status = ServiceStatus.DELETED
        service.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Service soft deleted",
            service_id=service_id,
            business_id=service.business_id,
            name=service.name,
        )
        return True
