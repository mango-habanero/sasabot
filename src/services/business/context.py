"""Business context service for data retrieval with caching."""

from src.configuration import app_logger
from src.data.entities.business import (
    Business,
    Configuration,
    Location,
    Promotion,
    Service,
    ServiceCategory,
)
from src.data.repositories import (
    BusinessRepository,
    ConfigurationRepository,
    LocationRepository,
    PromotionRepository,
    ServiceCategoryRepository,
    ServiceRepository,
)
from src.exceptions import ResourceNotFoundError


class ContextService:
    def __init__(
        self,
        business_repository: BusinessRepository,
        configuration_repository: ConfigurationRepository,
        location_repository: LocationRepository,
        service_category_repository: ServiceCategoryRepository,
        service_repository: ServiceRepository,
        promotion_repository: PromotionRepository,
    ):
        self.business_repo = business_repository
        self.config_repo = configuration_repository
        self.location_repo = location_repository
        self.category_repo = service_category_repository
        self.service_repo = service_repository
        self.promotion_repo = promotion_repository

    def get_active_promotions(self, business_id: int) -> list[Promotion]:
        promotions = self.promotion_repo.get_active_by_business_id(business_id)

        app_logger.debug(
            "Active promotions retrieved",
            business_id=business_id,
            count=len(promotions),
        )
        return promotions

    def get_all_services(self, business_id: int) -> list[Service]:
        services = self.service_repo.get_by_business_id(business_id)

        app_logger.debug(
            "All services retrieved",
            business_id=business_id,
            count=len(services),
        )
        return services

    def get_business(self, business_id: int) -> Business:
        business = self.business_repo.get_by_id(business_id)
        if not business:
            raise ResourceNotFoundError("business", resource_id=business_id)

        app_logger.debug(
            "Business retrieved", business_id=business_id, name=business.name
        )
        return business

    def get_categories(self, business_id: int) -> list[ServiceCategory]:
        categories = self.category_repo.get_by_business_id(business_id)

        app_logger.debug(
            "Service categories retrieved",
            business_id=business_id,
            count=len(categories),
        )
        return categories

    def get_configuration(self, business_id: int) -> Configuration:
        configuration = self.config_repo.get_by_business_id(business_id)
        if not configuration:
            raise ResourceNotFoundError("configuration", business_id=business_id)

        app_logger.debug("Configuration retrieved", business_id=business_id)
        return configuration

    def get_primary_location(self, business_id: int) -> Location:
        location = self.location_repo.get_primary_location(business_id)
        if not location:
            raise ResourceNotFoundError("primary_location", business_id=business_id)

        app_logger.debug(
            "Primary location retrieved",
            business_id=business_id,
            location_name=location.name,
        )
        return location

    def get_service_by_id(self, business_id: int, service_id: int) -> Service:
        service = self.service_repo.get_by_id(service_id)
        if not service or service.business_id != business_id:
            raise ResourceNotFoundError(
                "service",
                resource_id=service_id,
                business_id=business_id,
            )

        app_logger.debug(
            "Service retrieved",
            business_id=business_id,
            service_id=service_id,
            service_name=service.name,
        )
        return service

    def get_services_by_category(
        self, business_id: int, category_id: int
    ) -> list[Service]:
        services = self.service_repo.get_by_category_id(category_id)

        if services and services[0].business_id != business_id:
            raise ResourceNotFoundError(
                "category",
                resource_id=category_id,
                business_id=business_id,
            )

        app_logger.debug(
            "Services by category retrieved",
            business_id=business_id,
            category_id=category_id,
            count=len(services),
        )
        return services
