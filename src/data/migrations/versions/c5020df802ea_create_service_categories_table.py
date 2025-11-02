"""create service categories table.

Revision ID: c5020df802ea
Revises: bf42aa0d1779
Create Date: 2025-11-02 11:42:01.231715

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "c5020df802ea"
down_revision: Union[str, Sequence[str], None] = "bf42aa0d1779"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "service_categories",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", "DELETED", name="categorystatus"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_service_categories_business_id_businesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_categories")),
        sa.UniqueConstraint("business_id", "name", name="uq_business_category_name"),
    )
    with op.batch_alter_table("service_categories", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_service_categories_business_id"),
            ["business_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_service_categories_id"), ["id"], unique=False
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("service_categories", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_service_categories_id"))
        batch_op.drop_index(batch_op.f("ix_service_categories_business_id"))

    op.drop_table("service_categories")
    sa.Enum(name="categorystatus").drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
