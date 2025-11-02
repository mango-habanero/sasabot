"""create configurations table.

Revision ID: 9ea641f41a66
Revises: d33cdcf04f4f
Create Date: 2025-11-02 11:29:58.254015

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ea641f41a66"
down_revision: Union[str, Sequence[str], None] = "d33cdcf04f4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "configurations",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("deposit_percentage", sa.Float(), nullable=False),
        sa.Column("cancellation_window_hours", sa.Integer(), nullable=False),
        sa.Column("accepted_payment_methods", sa.JSON(), nullable=True),
        sa.Column("booking_advance_days", sa.Integer(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("buffer_time_minutes", sa.Integer(), nullable=False),
        sa.Column("auto_confirm_bookings", sa.Boolean(), nullable=False),
        sa.Column("custom_settings", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_configurations_business_id_businesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_configurations")),
    )
    with op.batch_alter_table("configurations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_configurations_business_id"), ["business_id"], unique=True
        )
        batch_op.create_index(batch_op.f("ix_configurations_id"), ["id"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("configurations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_configurations_id"))
        batch_op.drop_index(batch_op.f("ix_configurations_business_id"))

    op.drop_table("configurations")
    # ### end Alembic commands ###
