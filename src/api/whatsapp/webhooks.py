"""WhatsApp webhook endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from src.common.dependencies import get_session
from src.configuration import app_logger
from src.configuration.settings import settings
from src.data.dtos import WebhookPayload, WebhookResponse
from src.services.notification.whatsapp import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    app_logger.info(
        "Webhook verification request",
        mode=hub_mode,
        token_received=hub_verify_token[:10] + "...",  # Log partial token
    )

    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFICATION_TOKEN
    ):
        app_logger.info("Webhook verification successful")
        return Response(content=hub_challenge, media_type="text/plain")

    app_logger.warning(
        "Webhook verification failed",
        mode=hub_mode,
        token_match=hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFICATION_TOKEN,
    )
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp", response_model=WebhookResponse)
async def receive_webhook(
    payload: WebhookPayload,
    session: Session = Depends(get_session),
) -> WebhookResponse:
    app_logger.info(
        "Webhook received",
        entry_count=len(payload.entry),
        object_type=payload.object,
    )

    # Process webhook
    webhook_service = WebhookService(session)
    processed_count = await webhook_service.process_webhook(payload)

    app_logger.info(
        "Webhook processed successfully",
        messages_processed=processed_count,
    )

    # WhatsApp expects 200 OK quickly
    return WebhookResponse(status="ok")
