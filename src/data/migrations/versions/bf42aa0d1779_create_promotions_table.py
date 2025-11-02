"""create promotions table.

Revision ID: bf42aa0d1779
Revises: 076d7ca62164
Create Date: 2025-11-02 11:40:04.315468

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "bf42aa0d1779"
down_revision: Union[str, Sequence[str], None] = "076d7ca62164"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "promotions",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "promotion_type",
            sa.Enum(
                "PERCENTAGE_DISCOUNT",
                "FIXED_AMOUNT",
                "BOGO",
                "FREE_ADDON",
                name="promotiontype",
            ),
            nullable=False,
        ),
        sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("recurrence_rule", sa.JSON(), nullable=True),
        sa.Column("applicable_service_ids", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "INACTIVE", "ARCHIVED", "DELETED", name="promotionstatus"
            ),
            nullable=True,
        ),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("current_redemptions", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_promotions_business_id_businesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_promotions")),
    )
    with op.batch_alter_table("promotions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_promotions_business_id"), ["business_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_promotions_id"), ["id"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("promotions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_promotions_id"))
        batch_op.drop_index(batch_op.f("ix_promotions_business_id"))

    op.drop_table("promotions")
    sa.Enum(name="promotionstatus").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="promotiontype").drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
