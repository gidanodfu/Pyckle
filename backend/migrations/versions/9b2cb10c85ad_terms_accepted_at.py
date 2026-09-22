"""terms accepted at

Revision ID: 9b2cb10c85ad
Revises: 3715a0d52953
Create Date: 2026-09-14 06:24:29.922531

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '9b2cb10c85ad'
down_revision: str | None = '3715a0d52953'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fecha de aceptación de Términos y Condiciones en el registro.
    # Los índices compuestos de la migración anterior se definen solo en SQL,
    # por lo que Alembic no debe eliminarlos al comparar los modelos.
    op.add_column(
        'users',
        sa.Column('terms_accepted_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('users', 'terms_accepted_at')
