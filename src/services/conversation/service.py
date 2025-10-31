"""Conversation service for handling message flows and session management."""

from src.configuration import app_logger
from src.data.enums import ConversationState, MessageType
from src.data.repositories import (
    BookingRepository,
    ConversationSessionRepository,
    MessageRepository,
)
from src.services.conversation.handlers import (
    BookingConfirmHandler,
    BookingDateTimeHandler,
    BookingSelectServiceHandler,
    IdleStateHandler,
    PaymentInitiatedHandler,
    PaymentPendingHandler,
)
from src.services.conversation.state_machine import StateMachine
from src.services.notification.whatsapp.client import WhatsAppClient
from src.services.payment.safaricom import DarajaClient
from src.utilities import normalize_phone_number


class ConversationService:
    """Service for managing conversation flows and responses."""

    def __init__(
        self,
        session_repository: ConversationSessionRepository,
        message_repository: MessageRepository,
        whatsapp_client: WhatsAppClient,
    ):
        self.session_repo = session_repository
        self.message_repo = message_repository
        self.whatsapp_client = whatsapp_client

        # Initialize state machine
        self.state_machine = StateMachine(session_repository=session_repository)

        # Register state handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all state handlers with the state machine."""
        # Register IDLE handler
        self.state_machine.register_handler(
            state=ConversationState.IDLE,
            handler=IdleStateHandler(),
        )

        self.state_machine.register_handler(
            state=ConversationState.BOOKING_SELECT_SERVICE,
            handler=BookingSelectServiceHandler(),
        )

        self.state_machine.register_handler(
            state=ConversationState.BOOKING_SELECT_DATETIME,
            handler=BookingDateTimeHandler(),
        )

        booking_repo = BookingRepository(self.session_repo.session)
        self.state_machine.register_handler(
            state=ConversationState.BOOKING_CONFIRM,
            handler=BookingConfirmHandler(booking_repository=booking_repo),
        )

        daraja_client = DarajaClient()
        self.state_machine.register_handler(
            state=ConversationState.PAYMENT_INITIATED,
            handler=PaymentInitiatedHandler(
                booking_repository=booking_repo,
                daraja_client=daraja_client,
            ),
        )

        self.state_machine.register_handler(
            state=ConversationState.PAYMENT_PENDING,
            handler=PaymentPendingHandler(booking_repository=booking_repo),
        )

        # Additional handlers will be registered here as they're built
        app_logger.info("State handlers registered")

    async def handle_message(
        self,
        phone_number: str,
        message_content: str,
        customer_name: str | None = None,
    ) -> None:
        app_logger.info(
            "Processing message",
            phone_number=phone_number,
            content_preview=message_content[:50],
        )

        phone_number = normalize_phone_number(phone_number)
        session = self.session_repo.get_by_phone(phone_number)

        # Explicit session creation if needed
        if not session:
            session = self.session_repo.create(phone_number)
            if not session:
                app_logger.error(
                    "Failed to create conversation session",
                    phone_number=phone_number,
                )
                return

            app_logger.info(
                "New conversation session created",
                session_id=session.id,
                phone_number=phone_number,
                state=session.state.value,
            )

        # Execute state handler to get response
        try:
            response: dict = await self.state_machine.execute_state_handler(
                session=session,
                message_content=message_content,
                customer_name=customer_name,
            )
        except Exception as e:
            app_logger.error(
                "State handler execution failed",
                session_id=session.id,
                state=session.state.value,
                error=str(e),
            )
            # Fallback response
            response = {
                "text": "I apologize, but I'm having trouble processing your request. "
                "Please try again in a moment."
            }

        # Send response via WhatsApp
        await self._send_response(
            phone_number=phone_number,
            response=response,
            customer_name=customer_name,
        )

        app_logger.info(f"RESPONSE SENT: {response}")

        # Handle context updates if requested by handler (before state transition)
        if "update_context" in response and session.id is not None:
            try:
                context_updates: dict = response["update_context"]
                if not isinstance(context_updates, dict):
                    app_logger.error(
                        "Invalid update_context type", type=type(context_updates)
                    )
                else:
                    self.session_repo.merge_context(session.id, context_updates)
                    app_logger.info(
                        "Session context updated",
                        session_id=session.id,
                        updates=list(context_updates.keys()),
                    )
            except Exception as e:
                app_logger.error(
                    "Context update failed",
                    session_id=session.id,
                    error=str(e),
                )

        # Handle state transition if requested by handler
        if "transition_to" in response:
            if session.id is None:
                app_logger.error("Session ID is None, cannot transition state")
                return

            try:
                new_state = response["transition_to"]
                if not isinstance(new_state, ConversationState):
                    app_logger.error("Invalid transition_to type", type=type(new_state))
                    return

                # Perform state transition
                self.state_machine.transition_to(
                    session_id=session.id,
                    new_state=new_state,
                )
                app_logger.info(
                    "State transition completed",
                    session_id=session.id,
                    previous_state=session.state.value,
                    new_state=new_state.value,
                )

                # Immediately execute the new state's handler
                app_logger.info(
                    "Executing new state handler after transition",
                    session_id=session.id,
                    new_state=new_state.value,
                )

                # Refresh session to get updated state
                session = self.session_repo.get_by_phone(phone_number)
                if not session:
                    app_logger.error(
                        "Session not found after transition", phone_number=phone_number
                    )
                    return

                # Execute handler for the new state
                new_response = await self.state_machine.execute_state_handler(
                    session=session,
                    message_content=message_content,
                    customer_name=customer_name,
                )

                # Send the new state's response
                await self._send_response(
                    phone_number=phone_number,
                    response=new_response,
                    customer_name=customer_name,
                )

                # Handle any context updates from the new handler
                if "update_context" in new_response and session.id is not None:
                    try:
                        new_context_updates: dict = new_response["update_context"]
                        if not isinstance(new_context_updates, dict):
                            app_logger.error(
                                "Invalid update_context type from new handler",
                                type=type(new_context_updates),
                            )
                        else:
                            self.session_repo.merge_context(
                                session.id, new_context_updates
                            )
                            app_logger.info(
                                "Session context updated from new handler",
                                session_id=session.id,
                                updates=list(new_context_updates.keys()),
                            )
                    except Exception as e:
                        app_logger.error(
                            "Context update failed from new handler",
                            session_id=session.id,
                            error=str(e),
                        )

            except Exception as e:
                app_logger.error(
                    "State transition or new handler execution failed",
                    session_id=session.id,
                    target_state=response.get("transition_to"),
                    error=str(e),
                )

    async def _send_response(
        self,
        phone_number: str,
        response: dict,
        customer_name: str | None = None,
    ) -> None:
        try:
            # Determine message type and send accordingly
            if "text" in response:
                # Send text message
                api_response = await self.whatsapp_client.send_text(
                    to=phone_number,
                    text=response["text"],
                )
                message_type = MessageType.TEXT
                content = response["text"]

            elif "buttons" in response:
                # Send button message
                btn_data = response["buttons"]
                api_response = await self.whatsapp_client.send_buttons(
                    to=phone_number,
                    body_text=btn_data["body"],
                    buttons=btn_data["buttons"],
                    header_text=btn_data.get("header"),
                    footer_text=btn_data.get("footer"),
                )
                message_type = MessageType.BUTTON
                # Store button content summary
                button_ids = [btn[0] for btn in btn_data["buttons"]]
                content = f"Buttons: {', '.join(button_ids)}"

            elif "list" in response:
                # Send list message
                list_data = response["list"]
                api_response = await self.whatsapp_client.send_list(
                    to=phone_number,
                    body_text=list_data["body"],
                    button_text=list_data["button_text"],
                    sections=list_data["sections"],
                    header_text=list_data.get("header"),
                    footer_text=list_data.get("footer"),
                )
                message_type = MessageType.LIST
                # Store list content summary
                total_rows = sum(len(s.get("rows", [])) for s in list_data["sections"])
                content = f"List with {total_rows} items"

            elif "document" in response:
                # Send document message
                doc_data = response["document"]
                api_response = await self.whatsapp_client.send_document(
                    to=phone_number,
                    document_url=doc_data["url"],
                    filename=doc_data["filename"],
                    caption=doc_data.get("caption"),
                )
                message_type = (
                    MessageType.TEXT
                )  # Use TEXT for documents (no DOCUMENT enum)
                content = f"Document: {doc_data['filename']}"

            else:
                app_logger.error(
                    "Invalid response format from handler",
                    phone_number=phone_number,
                    response_keys=list(response.keys()),
                )
                return

            # Save outbound message to database
            self.message_repo.save_outbound(
                customer_phone=phone_number,
                content=content,
                message_type=message_type,
                whatsapp_message_id=api_response.message_id,
                customer_name=customer_name,
            )

            app_logger.info(
                "Response sent successfully",
                phone_number=phone_number,
                message_type=message_type.value,
                whatsapp_message_id=api_response.message_id,
            )

        except Exception as e:
            app_logger.error(
                "Failed to send response",
                phone_number=phone_number,
                error=str(e),
            )
