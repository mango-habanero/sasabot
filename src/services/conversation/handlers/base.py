"""Base handler for conversation state handling."""

from abc import ABC, abstractmethod

from src.data.entities.conversation_session import ConversationSession


class BaseStateHandler(ABC):
    """Abstract base class for all state handlers."""

    @abstractmethod
    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        """
        Handle a message in this state.

        Must be implemented by all concrete handlers.

        :param session: Current conversation session
        :param message_content: User's message content
        :param customer_name: Customer name (optional)
        :return: Response dict with 'text' or 'interactive' keys
            - {'text': 'response message'} for simple text
            - {'interactive': Interactive(...)} for buttons/lists
        """
        pass
