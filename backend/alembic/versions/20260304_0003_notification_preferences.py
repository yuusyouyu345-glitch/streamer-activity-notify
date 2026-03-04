"""add notification preferences

Revision ID: 20260304_0003
Revises: 20260304_0002
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa

revision = "20260304_0003"
down_revision = "20260304_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("streamer_id", sa.BigInteger(), sa.ForeignKey("streamers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "user_id", "streamer_id", "platform", "event_type",
            name="uq_notification_preferences_scope",
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")
