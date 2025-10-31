"""create messages table.

Revision ID: f6f1743d252a
Revises:
Create Date: 2025-10-30 07:51:58.381992

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "f6f1743d252a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "messages",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_phone", AutoString(length=20), nullable=False),
        sa.Column("customer_name", AutoString(length=255), nullable=True),
        sa.Column(
            "direction",
            sa.Enum("INBOUND", "OUTBOUND", name="messagedirection"),
            nullable=True,
        ),
        sa.Column("external_id", AutoString(length=255), nullable=True),
        sa.Column(
            "message_type",
            sa.Enum("BUTTON", "INTERACTIVE", "LIST", "TEXT", name="messagetype"),
            nullable=False,
        ),
        sa.Column("content", sa.TEXT(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DELIVERED", "FAILED", "PENDING", "READ", "SENT", name="messagestatus"
            ),
            nullable=True,
        ),
        sa.Column("whatsapp_timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        sa.UniqueConstraint("external_id", name=op.f("uq_messages_external_id")),
    )
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_messages_customer_phone"), ["customer_phone"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_messages_id"), ["id"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_messages_id"))
        batch_op.drop_index(batch_op.f("ix_messages_customer_phone"))

    op.drop_table("messages")

    sa.Enum(name="messagedirection").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="messagetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="messagestatus").drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
