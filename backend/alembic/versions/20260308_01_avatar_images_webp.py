"""avatar images webp

Revision ID: 20260308_01
Revises: 20260307_03
Create Date: 2026-03-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260308_01"
down_revision = "20260307_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("avatar_200_path", sa.String(length=255), nullable=True))
        batch.drop_column("avatar_path")

    op.create_table(
        "avatar_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "size", name="uq_avatar_images_user_size"),
    )
    op.create_index("ix_avatar_images_user_id", "avatar_images", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_avatar_images_user_id", table_name="avatar_images")
    op.drop_table("avatar_images")

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("avatar_path", sa.String(length=255), nullable=True))
        batch.drop_column("avatar_200_path")
