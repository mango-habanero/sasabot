"""Database dependencies."""

from collections.abc import Generator

from sqlmodel import Session, create_engine
from structlog import get_logger

from src.configuration.settings import settings

logger = get_logger(__name__)

# create an engine once at module level
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # Log SQL in dev mode
)


def get_session() -> Generator[Session, None, None]:
    """
    Provides a generator function to manage the database session lifecycle.
    This function creates a new session, yields it to the caller, and ensures
    its proper closure after use.

    Yields:
        Generator[Session, None, None]: A generator that yields an SQLAlchemy Session
        instance for database operations and ensures it is properly closed afterward.
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
