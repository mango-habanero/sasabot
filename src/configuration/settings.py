from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import app_logger


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    BASE_DIR: Final[Path] = Path(__file__).parent.parent.parent
    CORS_ORIGINS: list[AnyUrl] | str = Field(
        default=["http://localhost:5173"],
        description="List of allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    ENVIRONMENT: Literal["development", "production"] = Field(
        default="development", description="Application environment"
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    STRUCTURED_LOGGING_ENABLED: bool = Field(default=False, description="Use JSON logging format")


@lru_cache
def get_settings() -> Settings:
    _settings = Settings()
    if _settings.ENVIRONMENT == "development" or _settings.LOG_LEVEL == "DEBUG":
        app_logger.info("Running with settings:")
        for k, v in _settings.__dict__.items():
            app_logger.info(f"{k}= {v}")
    return _settings

settings = get_settings()
