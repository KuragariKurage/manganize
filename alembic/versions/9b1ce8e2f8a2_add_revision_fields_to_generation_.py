"""add revision fields to generation_history

Revision ID: 9b1ce8e2f8a2
Revises: 1c55dba4dd75
Create Date: 2026-02-08 15:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b1ce8e2f8a2"
down_revision: Union[str, Sequence[str], None] = "1c55dba4dd75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("generation_history") as batch_op:
        batch_op.add_column(
            sa.Column(
                "generation_type",
                sa.String(length=20),
                nullable=False,
                server_default="initial",
            )
        )
        batch_op.add_column(
            sa.Column("parent_generation_id", sa.String(length=36), nullable=True)
        )
        batch_op.add_column(sa.Column("revision_payload", sa.JSON(), nullable=True))
        batch_op.create_index(
            "idx_generation_type",
            ["generation_type"],
            unique=False,
        )
        batch_op.create_index(
            "idx_parent_generation_id",
            ["parent_generation_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_generation_history_parent_generation",
            "generation_history",
            ["parent_generation_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("generation_history") as batch_op:
        batch_op.drop_constraint(
            "fk_generation_history_parent_generation",
            type_="foreignkey",
        )
        batch_op.drop_index("idx_parent_generation_id")
        batch_op.drop_index("idx_generation_type")
        batch_op.drop_column("revision_payload")
        batch_op.drop_column("parent_generation_id")
        batch_op.drop_column("generation_type")
