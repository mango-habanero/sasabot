"""Repository for Configuration entity operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.configuration import app_logger
from src.data.entities.business import Configuration


class ConfigurationRepository:
    """Repository for Configuration entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        deposit_percentage: float = 30.0,
        cancellation_window_hours: int = 6,
        accepted_payment_methods: list | None = None,
        booking_advance_days: int = 30,
        slot_duration_minutes: int = 15,
        buffer_time_minutes: int = 0,
        auto_confirm_bookings: bool = False,
        custom_settings: dict | None = None,
    ) -> Configuration | None:
        try:
            configuration = Configuration(
                business_id=business_id,
                deposit_percentage=deposit_percentage,
                cancellation_window_hours=cancellation_window_hours,
                accepted_payment_methods=accepted_payment_methods or ["mpesa"],
                booking_advance_days=booking_advance_days,
                slot_duration_minutes=slot_duration_minutes,
                buffer_time_minutes=buffer_time_minutes,
                auto_confirm_bookings=auto_confirm_bookings,
                custom_settings=custom_settings or {},
            )

            self.session.add(configuration)
            self.session.commit()
            self.session.refresh(configuration)

            app_logger.info(
                "Configuration created",
                configuration_id=configuration.id,
                business_id=business_id,
            )
            return configuration

        except IntegrityError as e:
            self.session.rollback()
            app_logger.warning(
                "Configuration creation failed - duplicate business_id or FK violation",
                business_id=business_id,
                error=str(e),
            )
            return None

    def get_by_business_id(self, business_id: int) -> Configuration | None:
        statement = select(Configuration).where(
            Configuration.business_id == business_id
        )
        return self.session.exec(statement).first()

    def update(self, configuration_id: int, **updates) -> bool:
        configuration = self.session.get(Configuration, configuration_id)
        if not configuration:
            app_logger.warning(
                "Configuration not found for update",
                configuration_id=configuration_id,
            )
            return False

        for field, value in updates.items():
            if hasattr(configuration, field):
                setattr(configuration, field, value)

        configuration.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Configuration updated",
            configuration_id=configuration_id,
            business_id=configuration.business_id,
            updated_fields=list(updates.keys()),
        )
        return True
