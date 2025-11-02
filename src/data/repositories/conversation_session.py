"""Repository for ConversationSession entity operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState


class ConversationSessionRepository:
    """Repository for ConversationSession entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        phone_number: str,
        context: dict | None = None,
        state: ConversationState = ConversationState.IDLE,
    ) -> ConversationSession | None:
        try:
            session = ConversationSession(
                context=context or {},
                business_id=business_id,
                phone_number=phone_number,
                state=state,
            )

            self.session.add(session)
            self.session.commit()
            self.session.refresh(session)

            app_logger.info(
                "Conversation session created",
                business_id=business_id,
                phone_number=phone_number,
                session_id=session.id,
                state=state.value,
            )
            return session

        except IntegrityError:
            self.session.rollback()
            app_logger.warning(
                "Conversation session already exists",
                phone_number=phone_number,
            )
            return None
        except ValueError as e:
            self.session.rollback()
            app_logger.error(
                "Invalid phone number format",
                phone_number=phone_number,
                error=str(e),
            )
            return None

    def get_by_phone(self, phone_number: str) -> ConversationSession | None:
        statement = select(ConversationSession).where(
            ConversationSession.phone_number == phone_number
        )
        return self.session.exec(statement).first()

    def update_state(
        self,
        session_id: int,
        new_state: ConversationState,
    ) -> bool:
        session = self.session.get(ConversationSession, session_id)
        if not session:
            app_logger.warning(
                "Session not found for state update",
                session_id=session_id,
            )
            return False

        session.state = new_state
        session.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Conversation state updated",
            session_id=session_id,
            new_state=new_state.value,
        )
        return True

    def update_context(
        self,
        session_id: int,
        context: dict,
    ) -> bool:
        session = self.session.get(ConversationSession, session_id)
        if not session:
            app_logger.warning(
                "Session not found for context update",
                session_id=session_id,
            )
            return False

        session.context = context
        session.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Conversation context updated",
            session_id=session_id,
            context_keys=list(context.keys()),
        )
        return True

    def merge_context(
        self,
        session_id: int,
        context_updates: dict,
    ) -> bool:
        session = self.session.get(ConversationSession, session_id)
        if not session:
            app_logger.warning(
                "Session not found for context merge",
                session_id=session_id,
            )
            return False

        # Merge new data into existing context
        session.context = {**session.context, **context_updates}
        session.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        app_logger.info(
            "Conversation context merged",
            session_id=session_id,
            updated_keys=list(context_updates.keys()),
        )
        return True
