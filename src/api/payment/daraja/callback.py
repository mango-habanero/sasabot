"""Daraja M-Pesa callback endpoints."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.common.dependencies import get_session
from src.configuration import app_logger
from src.data.dtos.responses import DarajaCallbackPayload
from src.data.repositories import BookingRepository
from src.services.notification.whatsapp import WhatsAppClient
from src.services.payment.safaricom import DarajaCallbackService

router = APIRouter(prefix="/daraja")


@router.post("/callback")
async def daraja_callback(
    payload: DarajaCallbackPayload,
    session: Session = Depends(get_session),
) -> dict:
    app_logger.info(
        "Daraja callback received",
        checkout_request_id=payload.body.stk_callback.checkout_request_id,
        result_code=payload.body.stk_callback.result_code,
    )

    try:
        booking_repo = BookingRepository(session)
        whatsapp_client = WhatsAppClient()
        callback_service = DarajaCallbackService(
            booking_repository=booking_repo,
            whatsapp_client=whatsapp_client,
        )

        await callback_service.process_callback(payload)

        app_logger.info("Daraja callback processed successfully")

        return {"ResultCode": 0, "ResultDesc": "Success"}

    except Exception as e:
        app_logger.error(
            "Error processing Daraja callback",
            error=str(e),
            checkout_request_id=payload.body.stk_callback.checkout_request_id,
        )

        return {"ResultCode": 0, "ResultDesc": "Accepted"}
