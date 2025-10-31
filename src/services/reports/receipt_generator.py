import tempfile
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas

from src.configuration import app_logger
from src.data.entities.booking import Booking


class ReceiptPDFGenerator:
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 50
    BRAND_COLOR = colors.HexColor("#E91E63")
    DARK_GRAY = colors.HexColor("#333333")
    LIGHT_GRAY = colors.HexColor("#F5F5F5")

    def __init__(self):
        self.styles = getSampleStyleSheet()

    def generate(self, booking: Booking) -> Path:
        timestamp = int(datetime.now(timezone.utc).timestamp())
        filename = f"receipt_{booking.booking_reference}_{timestamp}.pdf"
        filepath = Path(tempfile.gettempdir()) / filename

        app_logger.info(
            "Generating PDF receipt",
            booking_id=booking.id,
            booking_reference=booking.booking_reference,
            filepath=str(filepath),
        )

        c = canvas.Canvas(str(filepath), pagesize=A4)

        y_position = self.PAGE_HEIGHT - self.MARGIN
        y_position = self._draw_header(c, y_position)
        y_position = self._draw_booking_info(c, booking, y_position)
        y_position = self._draw_service_details(c, booking, y_position)
        y_position = self._draw_payment_summary(c, booking, y_position)
        self._draw_location(c, y_position)
        self._draw_footer(c)

        c.save()

        app_logger.info(
            "PDF receipt generated",
            booking_id=booking.id,
            filepath=str(filepath),
        )

        return filepath

    def _draw_header(self, c: canvas.Canvas, y: float) -> float:
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(self.MARGIN, y, "💅 Glow Haven Beauty Lounge")

        y -= 30
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(self.MARGIN, y, "BOOKING RECEIPT")

        y -= 10
        c.setStrokeColor(self.BRAND_COLOR)
        c.setLineWidth(2)
        c.line(self.MARGIN, y, self.PAGE_WIDTH - self.MARGIN, y)

        y -= 5
        c.setStrokeColor(self.LIGHT_GRAY)
        c.setLineWidth(1)
        c.line(self.MARGIN, y, self.PAGE_WIDTH - self.MARGIN, y)

        return y - 30

    def _draw_booking_info(self, c: canvas.Canvas, booking: Booking, y: float) -> float:
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.MARGIN, y, "BOOKING INFORMATION")

        y -= 20
        c.setFont("Helvetica", 10)

        info = [
            f"Booking Reference: {booking.booking_reference}",
            f"Customer Name: {booking.customer_name or 'N/A'}",
            f"Customer Phone: {booking.customer_phone}",
            f"Receipt Date: {datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p')}",
        ]

        for line in info:
            c.drawString(self.MARGIN + 20, y, line)
            y -= 15

        return y - 10

    def _draw_service_details(
        self, c: canvas.Canvas, booking: Booking, y: float
    ) -> float:
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.MARGIN, y, "SERVICE DETAILS")

        y -= 20
        c.setFont("Helvetica", 10)

        details = [
            f"Service: {booking.service_name}",
            f"Category: {booking.service_category}",
            f"Duration: {booking.service_duration}",
            f"Appointment: {booking.appointment_datetime_display}",
        ]

        for line in details:
            c.drawString(self.MARGIN + 20, y, line)
            y -= 15

        return y - 10

    def _draw_payment_summary(
        self, c: canvas.Canvas, booking: Booking, y: float
    ) -> float:
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.MARGIN, y, "PAYMENT SUMMARY")

        y -= 20
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica", 10)

        summary = [
            f"Total Service Price: KES {booking.service_price:,}",
            f"Deposit Paid (30%): KES {booking.deposit_amount:,}",
            f"Balance Due on Visit: KES {booking.balance_amount:,}",
            "",
            "Payment Method: M-Pesa",
            f"M-Pesa Receipt: {booking.mpesa_receipt_number or 'Processing'}",
        ]

        if booking.payment_completed_at:
            payment_time = booking.payment_completed_at.strftime(
                "%B %d, %Y at %I:%M %p"
            )
            summary.append(f"Payment Date: {payment_time}")

        for line in summary:
            if line:
                c.drawString(self.MARGIN + 20, y, line)
            y -= 15

        y -= 10
        c.setFillColor(self.LIGHT_GRAY)
        c.rect(self.MARGIN, y, self.PAGE_WIDTH - 2 * self.MARGIN, 40, fill=1, stroke=0)

        y -= 25
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 12)
        total_text = f"TOTAL PAID: KES {booking.deposit_amount:,}"
        c.drawString(self.MARGIN + 20, y, total_text)

        return y - 30

    def _draw_location(self, c: canvas.Canvas, y: float) -> float:
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.MARGIN, y, "VISIT US AT")

        y -= 20
        c.setFont("Helvetica", 10)

        location = [
            "Glow Haven Beauty Lounge",
            "1st Floor, Valley Arcade Mall",
            "Nairobi, Kenya",
            "",
            "📞 +254 712 345 678",
            "📧 info@glowhavenbeauty.co.ke",
            "📱 @glowhavenbeautylounge",
        ]

        for line in location:
            if line:
                c.drawString(self.MARGIN + 20, y, line)
            y -= 15

        return y - 10

    def _draw_footer(self, c: canvas.Canvas) -> None:
        y = self.MARGIN + 40

        c.setStrokeColor(self.LIGHT_GRAY)
        c.setLineWidth(1)
        c.line(self.MARGIN, y, self.PAGE_WIDTH - self.MARGIN, y)

        y -= 20
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(
            self.PAGE_WIDTH / 2, y, "Thank you for choosing Glow Haven! 💅✨"
        )

        y -= 20
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            self.PAGE_WIDTH / 2,
            y,
            "Cancellations must be made 6 hours in advance | Your glow, our craft",
        )
