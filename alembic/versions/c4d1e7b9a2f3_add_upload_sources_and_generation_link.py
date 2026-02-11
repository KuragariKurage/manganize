"""add upload_sources and source_upload_id link

Revision ID: c4d1e7b9a2f3
Revises: 9b1ce8e2f8a2
Create Date: 2026-02-11 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4d1e7b9a2f3"
down_revision: Union[str, Sequence[str], None] = "9b1ce8e2f8a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("upload_sources"):
        op.create_table(
            "upload_sources",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("object_key", sa.String(length=512), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=255), nullable=True),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("object_key"),
        )
        inspector = sa.inspect(bind)

    existing_upload_source_indexes = {
        index["name"] for index in inspector.get_indexes("upload_sources")
    }
    if "idx_upload_sources_created_at" not in existing_upload_source_indexes:
        op.create_index(
            "idx_upload_sources_created_at",
            "upload_sources",
            ["created_at"],
            unique=False,
        )
    if "idx_upload_sources_expires_at" not in existing_upload_source_indexes:
        op.create_index(
            "idx_upload_sources_expires_at",
            "upload_sources",
            ["expires_at"],
            unique=False,
        )

    generation_columns = {
        column["name"] for column in inspector.get_columns("generation_history")
    }
    if "source_upload_id" not in generation_columns:
        with op.batch_alter_table("generation_history") as batch_op:
            batch_op.add_column(
                sa.Column("source_upload_id", sa.String(length=36), nullable=True)
            )
            batch_op.create_index(
                "idx_source_upload_id",
                ["source_upload_id"],
                unique=False,
            )
            batch_op.create_foreign_key(
                "fk_generation_history_source_upload",
                "upload_sources",
                ["source_upload_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("generation_history") as batch_op:
        batch_op.drop_constraint(
            "fk_generation_history_source_upload",
            type_="foreignkey",
        )
        batch_op.drop_index("idx_source_upload_id")
        batch_op.drop_column("source_upload_id")

    op.drop_index("idx_upload_sources_expires_at", table_name="upload_sources")
    op.drop_index("idx_upload_sources_created_at", table_name="upload_sources")
    op.drop_table("upload_sources")
