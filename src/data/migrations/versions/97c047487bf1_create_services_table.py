"""create services table.

Revision ID: 97c047487bf1
Revises: c5020df802ea
Create Date: 2025-11-02 11:43:33.607753

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "97c047487bf1"
down_revision: Union[str, Sequence[str], None] = "c5020df802ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "services",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(length=255), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "AVAILABLE", "UNAVAILABLE", "SEASONAL", "DELETED", name="servicestatus"
            ),
            nullable=True,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_services_business_id_businesses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["service_categories.id"],
            name=op.f("fk_services_category_id_service_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_services")),
        sa.UniqueConstraint(
            "business_id", "category_id", "name", name="uq_service_name"
        ),
    )
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_services_business_id"), ["business_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_services_category_id"), ["category_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_services_id"), ["id"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_services_id"))
        batch_op.drop_index(batch_op.f("ix_services_category_id"))
        batch_op.drop_index(batch_op.f("ix_services_business_id"))

    op.drop_table("services")
    sa.Enum(name="servicestatus").drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
