"""create locations table.

Revision ID: 076d7ca62164
Revises: 9ea641f41a66
Create Date: 2025-11-02 11:32:05.043056

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel import AutoString

# revision identifiers, used by Alembic.
revision: str = "076d7ca62164"
down_revision: Union[str, Sequence[str], None] = "9ea641f41a66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "locations",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("name", AutoString(length=255), nullable=False),
        sa.Column("address", sa.TEXT(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("operating_hours", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", "DELETED", name="locationstatus"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_locations_business_id_businesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_locations")),
        sa.UniqueConstraint("business_id", "name", name="uq_location_name"),
    )
    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_locations_business_id"), ["business_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_locations_id"), ["id"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_locations_id"))
        batch_op.drop_index(batch_op.f("ix_locations_business_id"))

    op.drop_table("locations")
    sa.Enum(name="locationstatus").drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
