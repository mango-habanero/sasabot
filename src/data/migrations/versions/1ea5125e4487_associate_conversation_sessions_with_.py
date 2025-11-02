"""associate conversation sessions with businesses.

Revision ID: 1ea5125e4487
Revises: 69fae4a6271f
Create Date: 2025-11-01 18:25:01.023850

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1ea5125e4487"
down_revision: Union[str, Sequence[str], None] = "69fae4a6271f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("conversation_sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("business_id", sa.Integer(), nullable=False))
        batch_op.create_index(
            batch_op.f("ix_conversation_sessions_business_id"),
            ["business_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_conversation_sessions_business_id_businesses"),
            "businesses",
            ["business_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("conversation_sessions", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_conversation_sessions_business_id_businesses"),
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_conversation_sessions_business_id"))
        batch_op.drop_column("business_id")

    # ### end Alembic commands ###
