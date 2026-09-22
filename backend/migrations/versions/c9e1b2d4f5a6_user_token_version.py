"""users.token_version: epoch de revocación de sesiones.

Revision ID: c9e1b2d4f5a6
Revises: a3f8c2d1e6b4
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9e1b2d4f5a6"
down_revision: Union[str, None] = "a3f8c2d1e6b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
