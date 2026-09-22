"""oauth_accounts: vínculo de identidades externas (OAuth) con usuarios locales.

Revision ID: a3f8c2d1e6b4
Revises: f2c1d3e4a5b6
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3f8c2d1e6b4"
down_revision: Union[str, None] = "f2c1d3e4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_oauth_accounts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth_accounts")),
        sa.UniqueConstraint(
            "provider", "provider_user_id", name="uq_oauth_accounts_provider_user"
        ),
    )
    op.create_index(
        "ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"], unique=False
    )
    op.create_index(
        "ix_oauth_accounts_provider_email",
        "oauth_accounts",
        ["provider", "email"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_oauth_accounts_provider_email", table_name="oauth_accounts")
    op.drop_index("ix_oauth_accounts_user_id", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")
