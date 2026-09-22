"""Ciclo de vida de reparación: estados técnicos, eventos, precios, costos e informes.

Revision ID: f2c1d3e4a5b6
Revises: 9b2cb10c85ad
Create Date: 2026-09-15

Reutiliza ``orders`` como la reparación. Los datos existentes se conservan:
``pending -> awaiting_receipt``, ``in_progress -> in_repair``, y
``order_status_history`` se migra a ``order_events``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2c1d3e4a5b6"
down_revision: Union[str, None] = "9b2cb10c85ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STATUS_MAP = (
    "CASE WHEN {col} = 'pending' THEN 'awaiting_receipt' "
    "WHEN {col} = 'in_progress' THEN 'in_repair' "
    "ELSE {col} END"
)

# Los estados nuevos no tienen equivalente exacto: se agrupan para el esquema viejo.
STATUS_MAP_DOWN = (
    "CASE WHEN {col} = 'awaiting_receipt' THEN 'pending' "
    "WHEN {col} IN ('received', 'diagnosis', 'waiting_customer', 'waiting_part', "
    "'in_repair', 'testing', 'ready') THEN 'in_progress' "
    "ELSE {col} END"
)


def upgrade() -> None:
    # --- orders: nuevo estado técnico, resultado y datos del proceso --------
    op.alter_column("orders", "total_amount", new_column_name="final_price")
    op.drop_constraint("order_status", "orders", type_="check")
    op.add_column("orders", sa.Column("result", sa.String(length=20), nullable=True))
    op.add_column(
        "orders", sa.Column("received_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("orders", sa.Column("diagnosis", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("work_performed", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("tests_performed", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("technician_notes", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("not_repairable_reason", sa.Text(), nullable=True))
    op.create_index("ix_orders_result", "orders", ["result"], unique=False)

    op.execute(
        "UPDATE orders SET status = "
        + STATUS_MAP.format(col="status")
        + " WHERE status IN ('pending', 'in_progress')"
    )
    op.execute(
        "UPDATE orders SET result = 'repaired' WHERE status = 'completed' "
        "AND result IS NULL"
    )
    op.execute(
        "UPDATE orders SET result = 'cancelled' WHERE status = 'cancelled' "
        "AND result IS NULL"
    )
    op.execute(
        "UPDATE orders SET received_at = created_at "
        "WHERE status NOT IN ('awaiting_receipt') AND received_at IS NULL"
    )

    # --- notifications: el check de tipos se maneja a nivel de aplicación ----
    op.drop_constraint("notification_type", "notifications", type_="check")

    # --- order_status_history -> order_events -------------------------------
    op.create_table(
        "order_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False, server_default="note"),
        sa.Column("old_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "visible_to_customer", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_events_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_order_events_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_events")),
    )
    op.create_index("ix_order_events_order_id", "order_events", ["order_id"], unique=False)
    op.create_index(
        "ix_order_events_visible_to_customer",
        "order_events",
        ["visible_to_customer"],
        unique=False,
    )
    op.execute(
        "INSERT INTO order_events "
        "(id, order_id, actor_id, event_type, old_status, new_status, description, "
        " metadata, visible_to_customer, created_at, updated_at) "
        "SELECT id, order_id, changed_by, 'status_changed', "
        + STATUS_MAP.format(col="from_status")
        + ", "
        + STATUS_MAP.format(col="to_status")
        + ", note, NULL, true, created_at, updated_at FROM order_status_history"
    )
    op.drop_table("order_status_history")

    # --- order_price_changes ------------------------------------------------
    op.create_table(
        "order_price_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("new_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_price_changes_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            name=op.f("fk_order_price_changes_requested_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by"],
            ["users.id"],
            name=op.f("fk_order_price_changes_decided_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_price_changes")),
    )
    op.create_index(
        "ix_order_price_changes_order_id", "order_price_changes", ["order_id"], unique=False
    )
    op.create_index(
        "ix_order_price_changes_status", "order_price_changes", ["status"], unique=False
    )

    # --- order_cost_items ---------------------------------------------------
    op.create_table(
        "order_cost_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="other"),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "visible_to_customer", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_cost_items_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_order_cost_items_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_cost_items")),
    )
    op.create_index("ix_order_cost_items_order_id", "order_cost_items", ["order_id"], unique=False)

    # --- repair_reports -----------------------------------------------------
    op.create_table(
        "repair_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column(
            "content_type", sa.String(length=80), nullable=False, server_default="application/pdf"
        ),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_repair_reports_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["generated_by"],
            ["users.id"],
            name=op.f("fk_repair_reports_generated_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repair_reports")),
        sa.UniqueConstraint(
            "order_id", "version", name="uq_repair_reports_order_version"
        ),
    )
    op.create_index("ix_repair_reports_order_id", "repair_reports", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_repair_reports_order_id", table_name="repair_reports")
    op.drop_table("repair_reports")
    op.drop_index("ix_order_cost_items_order_id", table_name="order_cost_items")
    op.drop_table("order_cost_items")
    op.drop_index("ix_order_price_changes_status", table_name="order_price_changes")
    op.drop_index("ix_order_price_changes_order_id", table_name="order_price_changes")
    op.drop_table("order_price_changes")

    # order_events -> order_status_history
    op.create_table(
        "order_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_status_history_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"],
            ["users.id"],
            name=op.f("fk_order_status_history_changed_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_status_history")),
    )
    op.create_index(
        op.f("ix_order_status_history_order_id"),
        "order_status_history",
        ["order_id"],
        unique=False,
    )
    op.execute(
        "INSERT INTO order_status_history "
        "(id, order_id, from_status, to_status, changed_by, note, created_at, updated_at) "
        "SELECT id, order_id, "
        + STATUS_MAP_DOWN.format(col="old_status")
        + ", "
        + STATUS_MAP_DOWN.format(col="new_status")
        + ", actor_id, description, created_at, updated_at FROM order_events"
    )
    op.drop_index("ix_order_events_visible_to_customer", table_name="order_events")
    op.drop_index("ix_order_events_order_id", table_name="order_events")
    op.drop_table("order_events")

    op.create_check_constraint(
        "notification_type",
        "notifications",
        "type IN ('quotation_created', 'quotation_accepted', 'order_status_changed', "
        "'message_new', 'review_created', 'system')",
    )

    op.drop_index("ix_orders_result", table_name="orders")
    op.drop_column("orders", "not_repairable_reason")
    op.drop_column("orders", "technician_notes")
    op.drop_column("orders", "tests_performed")
    op.drop_column("orders", "work_performed")
    op.drop_column("orders", "diagnosis")
    op.drop_column("orders", "received_at")
    op.drop_column("orders", "result")
    op.execute("UPDATE orders SET status = " + STATUS_MAP_DOWN.format(col="status"))
    op.create_check_constraint(
        "order_status",
        "orders",
        "status IN ('pending', 'in_progress', 'completed', 'cancelled')",
    )
    op.alter_column("orders", "final_price", new_column_name="total_amount")
