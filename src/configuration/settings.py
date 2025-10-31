"""Application settings."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Final, Literal

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configuration.logger import app_logger


def _parse_cors(v: Any) -> list[str]:
    """
    Parses the given value to extract a list of CORS origins. The input can be a string
    representing a list (JSON format or comma-separated), or an existing list of origins.
    Returns a processed list of trimmed and valid origins.

    :param v: Input value representing CORS origins. Can be a list, JSON array string,
        or a comma-separated string.
    :type v: Any
    :returns: A list of processed CORS origins in string format.
    :rtype: list[str]
    :raises ValueError: If the input value is not in a valid format or cannot be parsed.
    """
    if isinstance(v, str):
        if v.startswith("[") and v.endswith("]"):
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed]
            except json.JSONDecodeError:
                pass
        # treat as comma-separated
        return [item.strip() for item in v.split(",") if item.strip()]
    elif isinstance(v, list):
        return [str(item).strip() for item in v if item]
    else:
        raise ValueError(f"Invalid CORS origin format: {v}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # anthropic configuration
    ANTHROPIC_API_KEY: str = Field(description="Anthropic API key.")

    # daraja configuration
    DARAJA_BUSINESS_SHORTCODE: str = Field(description="Shortcode of the organization.")
    DARAJA_CERTIFICATE_PATH: str = Field(description="Path to the certificate file.")
    DARAJA_CALLBACK_URL: str = Field(
        description="Callback URL for M-Pesa payment notifications"
    )
    DARAJA_CONSUMER_KEY: str = Field(
        description="Consumer key retrieved from Daraja portal."
    )
    DARAJA_CONSUMER_SECRET: str = Field(
        description="Consumer secret retrieved from Daraja portal."
    )
    DARAJA_INITIATOR_NAME: str = Field(
        description="Username of an API user created on Mpesa portal."
    )
    DARAJA_INITIATOR_PASSWORD: str = Field(
        description="Password of an API user created on Mpesa portal."
    )
    DARAJA_PASSKEY: str = Field(description="Passkey retrieved from Daraja portal.")
    DARAJA_SANDBOX_PARTY_A: str = Field(
        description="Party A number retrieved from Daraja portal."
    )
    DARAJA_SANDBOX_PARTY_B: str = Field(
        description="Party B number retrieved from Daraja portal."
    )
    DARAJA_SANDBOX_PHONE_NUMBER: str = Field(
        description="Phone number of the organization."
    )
    DARAJA_URL: str = Field(description="Daraja API URL")

    # database configuration
    DATABASE_URL: str = Field(description="Database connection URL")

    # server configuration
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")
    BASE_DIR: Final[Path] = Path(__file__).parent.parent.parent
    BASE_URL: str = Field(default="http://localhost:8000", description="Base URL")
    CORS_ORIGINS: Annotated[list[str] | str, BeforeValidator(_parse_cors)]
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True, description="Allow credentials in CORS requests"
    )
    ENVIRONMENT: Literal["development", "production"] = Field(
        default="development", description="Application environment"
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    STRUCTURED_LOGGING_ENABLED: bool = Field(
        default=False, description="Use JSON logging format"
    )
    TIMEZONE: str = Field(
        default="Africa/Nairobi", description="Timezone for timestamps"
    )

    # Whatsapp configuration
    META_API_VERSION: str = Field(description="API version")
    WHATSAPP_ACCESS_TOKEN: str = Field(description="Whatsapp access token")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(description="Whatsapp phone number id")
    WHATSAPP_WEBHOOK_VERIFICATION_TOKEN: str = Field(
        description="Whatsapp webhook verification token"
    )

    _SECRET_FIELDS: set[str] = {
        "ANTHROPIC_API_KEY",
        "DARAJA_CONSUMER_KEY",
        "DARAJA_CONSUMER_SECRET",
        "DARAJA_INITIATOR_PASSWORD",
        "DARAJA_PASSKEY",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_WEBHOOK_VERIFICATION_TOKEN",
    }

    def model_dump_safe(self) -> dict[str, Any]:
        """Return settings dict with secrets redacted."""
        data = self.model_dump()
        for key in self._SECRET_FIELDS:
            if key in data:
                data[key] = "********"
        return data


@lru_cache
def get_settings() -> Settings:
    _settings = Settings()  # type: ignore[call-arg]
    if _settings.ENVIRONMENT == "development" and _settings.LOG_LEVEL == "DEBUG":
        app_logger.debug("Loaded application settings (secrets redacted):")
        for k, v in _settings.model_dump_safe().items():
            app_logger.debug(f"{k} = {v}")
    return _settings


settings = get_settings()
