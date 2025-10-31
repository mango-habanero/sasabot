"""create bookings table.

Revision ID: b44deb8b001b
Revises: 4468244ef687
Create Date: 2025-10-30 23:36:37.285803

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "b44deb8b001b"
down_revision: Union[str, Sequence[str], None] = "4468244ef687"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "bookings",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_reference", AutoString(length=20), nullable=False),
        sa.Column("customer_phone", AutoString(length=20), nullable=False),
        sa.Column("customer_name", AutoString(length=255), nullable=True),
        sa.Column("service_category", AutoString(length=100), nullable=False),
        sa.Column("service_name", AutoString(length=255), nullable=False),
        sa.Column("service_duration", AutoString(length=50), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=True),
        sa.Column("appointment_time", sa.Time(), nullable=True),
        sa.Column(
            "appointment_datetime_display", AutoString(length=255), nullable=False
        ),
        sa.Column("service_price", sa.Integer(), nullable=False),
        sa.Column("deposit_amount", sa.Integer(), nullable=False),
        sa.Column("balance_amount", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column(
            "payment_status",
            sa.Enum("PENDING", "PAID", "FAILED", name="paymentstatus"),
            nullable=True,
        ),
        sa.Column(
            "booking_status",
            sa.Enum(
                "PENDING", "CONFIRMED", "CANCELLED", "COMPLETED", name="bookingstatus"
            ),
            nullable=True,
        ),
        sa.Column("conversation_session_id", sa.Integer(), nullable=True),
        sa.Column("mpesa_checkout_request_id", AutoString(length=255), nullable=True),
        sa.Column("mpesa_receipt_number", AutoString(length=50), nullable=True),
        sa.Column("payment_completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_session_id"],
            ["conversation_sessions.id"],
            name=op.f("fk_bookings_conversation_session_id_conversation_sessions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bookings")),
    )
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_bookings_appointment_date"),
            ["appointment_date"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_bookings_booking_reference"),
            ["booking_reference"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_bookings_customer_phone"), ["customer_phone"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_bookings_id"), ["id"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookings_id"))
        batch_op.drop_index(batch_op.f("ix_bookings_customer_phone"))
        batch_op.drop_index(batch_op.f("ix_bookings_booking_reference"))
        batch_op.drop_index(batch_op.f("ix_bookings_appointment_date"))

    op.drop_table("bookings")

    sa.Enum(name="paymentstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="bookingstatus").drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
