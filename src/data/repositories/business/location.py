"""Repository for Location entity operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from src.configuration import app_logger
from src.data.entities.business import Location
from src.data.enums.business import LocationStatus


class LocationRepository:
    """Repository for Location entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        name: str,
        address: str,
        operating_hours: dict,
        is_primary: bool = False,
        status: LocationStatus = LocationStatus.ACTIVE,
    ) -> Location | None:
        try:
            location = Location(
                business_id=business_id,
                name=name,
                address=address,
                operating_hours=operating_hours,
                is_primary=is_primary,
                status=status,
            )

            self.session.add(location)
            self.session.commit()
            self.session.refresh(location)

            app_logger.info(
                "Location created",
                location_id=location.id,
                business_id=business_id,
                name=name,
                is_primary=is_primary,
            )
            return location

        except IntegrityError as e:
            self.session.rollback()
            app_logger.warning(
                "Location creation failed - duplicate name or FK violation",
                business_id=business_id,
                name=name,
                error=str(e),
            )
            return None

    def get_by_id(
        self, location_id: int, include_deleted: bool = False
    ) -> Location | None:
        statement = select(Location).where(Location.id == location_id)

        if not include_deleted:
            statement = statement.where(Location.status != LocationStatus.DELETED)

        return self.session.exec(statement).first()

    def get_by_business_id(
        self, business_id: int, include_deleted: bool = False
    ) -> list[Location]:
        statement = select(Location).where(Location.business_id == business_id)

        if not include_deleted:
            statement = statement.where(Location.status != LocationStatus.DELETED)

        # Primary location first, then by name
        statement = statement.order_by(col(Location.is_primary).desc(), Location.name)

        return list(self.session.exec(statement).all())

    def get_primary_location(self, business_id: int) -> Location | None:
        statement = (
            select(Location)
            .where(Location.business_id == business_id)
            .where(Location.is_primary)
            .where(Location.status != LocationStatus.DELETED)
        )

        return self.session.exec(statement).first()

    def soft_delete(self, location_id: int) -> bool:
        location = self.session.get(Location, location_id)
        if not location:
            app_logger.warning(
                "Location not found for soft delete",
                location_id=location_id,
            )
            return False

        location.status = LocationStatus.DELETED
        location.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Location soft deleted",
            location_id=location_id,
            business_id=location.business_id,
            name=location.name,
        )
        return True
