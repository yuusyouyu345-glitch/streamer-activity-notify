"""add source status table

Revision ID: 20260304_0004
Revises: 20260304_0003
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa

revision = "20260304_0004"
down_revision = "20260304_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_status",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source", sa.String(length=32), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("source_status")
