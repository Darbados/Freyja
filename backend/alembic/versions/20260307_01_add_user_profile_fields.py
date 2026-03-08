"""add user profile fields

Revision ID: 20260307_01
Revises: 
Create Date: 2026-03-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260307_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch.add_column(sa.Column("first_name", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("last_name", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("birthday", sa.Date(), nullable=True))
        batch.add_column(sa.Column("position", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("seniority", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("seniority")
        batch.drop_column("position")
        batch.drop_column("birthday")
        batch.drop_column("last_name")
        batch.drop_column("first_name")
        batch.drop_column("is_superuser")
