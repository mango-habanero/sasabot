"""Repository for Business entity operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.configuration import app_logger
from src.data.entities.business import Business
from src.data.enums.business import BusinessStatus


class BusinessRepository:
    """Repository for Business entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        name: str,
        slug: str,
        phone: str,
        whatsapp_phone_number_id: str,
        email: str | None = None,
        instagram_handle: str | None = None,
        website: str | None = None,
        booking_policy_text: str | None = None,
        status: BusinessStatus = BusinessStatus.ACTIVE,
    ) -> Business | None:
        try:
            business = Business(
                name=name,
                slug=slug,
                phone=phone,
                whatsapp_phone_number_id=whatsapp_phone_number_id,
                email=email,
                instagram_handle=instagram_handle,
                website=website,
                booking_policy_text=booking_policy_text,
                status=status,
            )

            self.session.add(business)
            self.session.commit()
            self.session.refresh(business)

            app_logger.info(
                "Business created",
                business_id=business.id,
                name=name,
                slug=slug,
            )
            return business

        except IntegrityError as e:
            self.session.rollback()
            app_logger.warning(
                "Business creation failed - duplicate slug or whatsapp_phone_number_id",
                slug=slug,
                whatsapp_phone_number_id=whatsapp_phone_number_id,
                error=str(e),
            )
            return None

    def get_by_id(
        self, business_id: int, include_deleted: bool = False
    ) -> Business | None:
        statement = select(Business).where(Business.id == business_id)

        if not include_deleted:
            statement = statement.where(Business.status != BusinessStatus.DELETED)

        return self.session.exec(statement).first()

    def get_by_whatsapp_number_id(
        self, whatsapp_phone_number_id: str, include_deleted: bool = False
    ) -> Business | None:
        statement = select(Business).where(
            Business.whatsapp_phone_number_id == whatsapp_phone_number_id
        )

        if not include_deleted:
            statement = statement.where(Business.status != BusinessStatus.DELETED)

        business = self.session.exec(statement).first()

        if business:
            app_logger.debug(
                "Business found by WhatsApp number ID",
                business_id=business.id,
                whatsapp_phone_number_id=whatsapp_phone_number_id,
            )

        return business

    def soft_delete(self, business_id: int) -> bool:
        business = self.session.get(Business, business_id)
        if not business:
            app_logger.warning(
                "Business not found for soft delete",
                business_id=business_id,
            )
            return False

        business.status = BusinessStatus.DELETED
        business.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Business soft deleted",
            business_id=business_id,
            name=business.name,
        )
        return True
