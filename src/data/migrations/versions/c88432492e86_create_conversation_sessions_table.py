"""create conversation sessions table.

Revision ID: c88432492e86
Revises:
Create Date: 2025-11-01 18:18:08.003394

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "c88432492e86"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "conversation_sessions",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("phone_number", AutoString(length=20), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "IDLE",
                "PROCESSING_INTENT",
                "BOOKING_SELECT_SERVICE",
                "BOOKING_SELECT_DATETIME",
                "BOOKING_CONFIRM",
                "PAYMENT_INITIATED",
                "PAYMENT_PENDING",
                "FEEDBACK_RATING",
                "FEEDBACK_COMMENT",
                name="conversationstate",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_sessions")),
    )
    with op.batch_alter_table("conversation_sessions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_conversation_sessions_id"), ["id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_conversation_sessions_phone_number"),
            ["phone_number"],
            unique=True,
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("conversation_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_conversation_sessions_phone_number"))
        batch_op.drop_index(batch_op.f("ix_conversation_sessions_id"))

    op.drop_table("conversation_sessions")
    sa.Enum(name="conversationstate").drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
