"""add device tokens and notification error message

Revision ID: 20260304_0002
Revises: 20260304_0001
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260304_0002"
down_revision = "20260304_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("error_message", sa.Text(), nullable=True))
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False, server_default="android"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "token", name="uq_device_tokens_user_token"),
    )


def downgrade() -> None:
    op.drop_table("device_tokens")
    op.drop_column("notifications", "error_message")
