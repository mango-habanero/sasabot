"""create businesses table.

Revision ID: 69fae4a6271f
Revises: c88432492e86
Create Date: 2025-11-01 18:23:44.348720

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "69fae4a6271f"
down_revision: Union[str, Sequence[str], None] = "c88432492e86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "businesses",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(length=255), nullable=False),
        sa.Column("slug", AutoString(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "INACTIVE", "SUSPENDED", "DELETED", name="businessstatus"
            ),
            nullable=True,
        ),
        sa.Column("email", AutoString(length=255), nullable=True),
        sa.Column("phone", AutoString(length=20), nullable=False),
        sa.Column("instagram_handle", AutoString(length=100), nullable=True),
        sa.Column("website", AutoString(length=255), nullable=True),
        sa.Column("booking_policy_text", sa.Text(), nullable=True),
        sa.Column("whatsapp_phone_number_id", AutoString(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_businesses")),
    )
    with op.batch_alter_table("businesses", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_businesses_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_businesses_slug"), ["slug"], unique=True)
        batch_op.create_index(
            batch_op.f("ix_businesses_whatsapp_phone_number_id"),
            ["whatsapp_phone_number_id"],
            unique=True,
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("businesses", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_businesses_whatsapp_phone_number_id"))
        batch_op.drop_index(batch_op.f("ix_businesses_slug"))
        batch_op.drop_index(batch_op.f("ix_businesses_id"))

    op.drop_table("businesses")
    sa.Enum(name="businessstatus").drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
