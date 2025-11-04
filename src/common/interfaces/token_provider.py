from abc import ABC, abstractmethod


class TokenProvider(ABC):
    """Abstract interface for token management services."""

    @abstractmethod
    async def get_valid_token(self) -> str:
        pass

    @abstractmethod
    async def invalidate_token(self) -> None:
        pass
