"""State machine for managing conversation flow and state transitions."""

from src.configuration import app_logger
from src.data.entities import ConversationSession
from src.data.enums import ConversationState
from src.data.repositories.conversation_session import ConversationSessionRepository
from src.exceptions import InvalidStateTransitionError
from src.services.conversation.handlers import BaseStateHandler

# valid state transitions (business rules)
VALID_TRANSITIONS: dict[ConversationState, list[ConversationState]] = {
    ConversationState.IDLE: [
        ConversationState.PROCESSING_INTENT,
        ConversationState.BOOKING_SELECT_SERVICE,
        ConversationState.FEEDBACK_RATING,
    ],
    ConversationState.PROCESSING_INTENT: [
        ConversationState.IDLE,
        ConversationState.BOOKING_SELECT_SERVICE,
        ConversationState.FEEDBACK_RATING,
    ],
    ConversationState.BOOKING_SELECT_SERVICE: [
        ConversationState.BOOKING_SELECT_DATETIME,
        ConversationState.IDLE,  # Cancel
    ],
    ConversationState.BOOKING_SELECT_DATETIME: [
        ConversationState.BOOKING_CONFIRM,
        ConversationState.BOOKING_SELECT_SERVICE,  # Go back
        ConversationState.IDLE,  # Cancel
    ],
    ConversationState.BOOKING_CONFIRM: [
        ConversationState.PAYMENT_INITIATED,
        ConversationState.BOOKING_SELECT_DATETIME,  # Go back
        ConversationState.IDLE,  # Cancel
    ],
    ConversationState.PAYMENT_INITIATED: [
        ConversationState.PAYMENT_PENDING,
        ConversationState.IDLE,  # Cancel/timeout
    ],
    ConversationState.PAYMENT_PENDING: [
        ConversationState.IDLE,  # Success or failure returns to idle
    ],
    ConversationState.FEEDBACK_RATING: [
        ConversationState.FEEDBACK_COMMENT,
        ConversationState.IDLE,  # Skip comment
    ],
    ConversationState.FEEDBACK_COMMENT: [
        ConversationState.IDLE,  # Done
    ],
}


def _validate_transition(
    current_state: ConversationState,
    next_state: ConversationState,
) -> bool:
    allowed_transitions = VALID_TRANSITIONS.get(current_state, [])
    return next_state in allowed_transitions


class StateMachine:
    """Manages conversation state transitions and handler execution."""

    def __init__(self, session_repository: ConversationSessionRepository):
        self.session_repo = session_repository
        self._handlers: dict[ConversationState, BaseStateHandler] = {}

    def register_handler(
        self, state: ConversationState, handler: BaseStateHandler
    ) -> None:
        self._handlers[state] = handler
        app_logger.debug("Handler registered", state=state.value)

    def transition_to(
        self,
        session_id: int,
        new_state: ConversationState,
    ) -> bool:
        session = self.session_repo.session.get(ConversationSession, session_id)
        if not session:
            app_logger.warning(
                "Session not found for state transition",
                session_id=session_id,
            )
            return False

        if not _validate_transition(session.state, new_state):
            error_msg = (
                f"Invalid state transition from {session.state.value} "
                f"to {new_state.value}"
            )
            app_logger.error(
                "Invalid state transition attempt",
                session_id=session_id,
                current_state=session.state.value,
                attempted_state=new_state.value,
            )
            raise InvalidStateTransitionError(
                message=error_msg,
                current_state=session.state.value,
                attempted_state=new_state.value,
            )

        success = self.session_repo.update_state(session_id, new_state)

        if success:
            app_logger.info(
                "State transition successful",
                session_id=session_id,
                previous_state=session.state.value,
                new_state=new_state.value,
            )

        return success

    async def execute_state_handler(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        handler = self._handlers.get(session.state)

        if not handler:
            app_logger.warning(
                "No handler registered for state",
                state=session.state.value,
                session_id=session.id,
            )
            return {
                "text": "I'm having trouble processing your request. Please try again."
            }

        app_logger.info(
            "Executing state handler",
            state=session.state.value,
            session_id=session.id,
        )

        return await handler.handle(session, message_content, customer_name)
