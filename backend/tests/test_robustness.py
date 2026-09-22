"""Robustez: casos extremos y errores controlados (sin 500 inesperados)."""

from pathlib import Path

import pytest
import redis

from app.core.config import get_settings
from tests.conftest import auth_header, drive_order, run_flow

pytestmark = pytest.mark.asyncio

BIG = "1000000000000"


class _BrokenRedis:
    def __getattr__(self, name):
        if name == "pipeline":
            # ``pipeline()`` es síncrono en redis.asyncio; una Redis caída debe
            # fallar al construirlo/ejecutarlo, no devolver una corrutina.
            def _raise_pipeline(*_args, **_kwargs):
                raise redis.RedisError("redis caído")

            return _raise_pipeline

        async def _raise(*_args, **_kwargs):
            raise redis.RedisError("redis caído")

        return _raise


async def test_admin_orders_list_ok(client, admin_token):
    response = await client.get("/api/v1/admin/orders", headers=auth_header(admin_token))
    assert response.status_code == 200, response.text
    assert "items" in response.json()


async def test_money_overflow_is_422(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready

    budget = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Presupuesto enorme",
            "description": "Debe rechazar montos fuera de rango.",
            "budget_min": BIG,
        },
    )
    assert budget.status_code == 422

    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    change = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": BIG, "reason": "Monto fuera de rango permitido."},
    )
    assert change.status_code == 422

    cost = await client.post(
        f"/api/v1/orders/{order_id}/costs",
        headers=auth_header(technician_token),
        json={"kind": "part", "description": "Costo enorme", "amount": BIG},
    )
    assert cost.status_code == 422


async def test_redis_down_returns_503(client, customer_token, monkeypatch):
    monkeypatch.setattr("app.core.ratelimit.get_redis", lambda: _BrokenRedis())
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "someone@test.dev", "password": "password12345"},
    )
    assert login.status_code == 503

    monkeypatch.setattr("app.core.ws_tickets.get_redis", lambda: _BrokenRedis())
    ticket = await client.post("/api/v1/ws/ticket", headers=auth_header(customer_token))
    assert ticket.status_code == 503


async def test_pending_price_blocks_not_repairable(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 240, "reason": "Daño adicional detectado en la placa."},
    )
    assert proposal.status_code == 201
    change_id = proposal.json()["id"]

    result = await client.post(
        f"/api/v1/orders/{order_id}/not-repairable",
        headers=auth_header(technician_token),
        json={
            "reason": "Daño irreparable confirmado en el componente principal.",
            "diagnosis": "Diagnóstico técnico detallado del daño encontrado.",
        },
    )
    assert result.status_code == 409

    # Cancelar cierra y rechaza el cambio pendiente.
    cancel = await client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_header(technician_token),
        json={"reason": "El cliente desistió del servicio"},
    )
    assert cancel.status_code == 200, cancel.text

    changes = await client.get(
        f"/api/v1/orders/{order_id}/price-changes", headers=auth_header(technician_token)
    )
    assert changes.json()[0]["status"] == "rejected"

    approve = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/approve",
        headers=auth_header(customer_token),
        json={},
    )
    assert approve.status_code == 409


async def test_not_repairable_before_receipt_is_400(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    response = await client.post(
        f"/api/v1/orders/{order_id}/not-repairable",
        headers=auth_header(technician_token),
        json={
            "reason": "Daño irreparable confirmado en el equipo.",
            "diagnosis": "Diagnóstico técnico detallado del daño.",
        },
    )
    assert response.status_code == 400


async def test_whitespace_only_fields_are_422(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={"title": "          ", "description": "Descripción válida del problema."},
    )
    assert request.status_code == 422

    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    cancel = await client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_header(customer_token),
        json={"reason": "               "},
    )
    assert cancel.status_code == 422


async def test_report_cleanup_on_internal_failure(
    client, customer_token, technician_ready, monkeypatch
):
    from app.domains.orders.service import OrderService

    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "ready")

    async def _boom(self, order_id):  # noqa: ANN001
        raise RuntimeError("fallo simulado tras escribir el PDF")

    monkeypatch.setattr(OrderService, "_archive_conversation", _boom)

    with pytest.raises(RuntimeError):
        await client.post(
            f"/api/v1/orders/{order_id}/complete",
            headers=auth_header(technician_token),
            json={
                "diagnosis": "Diagnóstico de prueba suficiente.",
                "work_performed": "Trabajo realizado de prueba.",
            },
        )

    reports_dir = Path(get_settings().storage_local_dir) / "reports" / str(order_id)
    assert not reports_dir.exists() or not list(reports_dir.glob("*.pdf"))


async def test_price_change_rejects_non_pending(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    reduction = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 120, "reason": "Repuesto más económico de lo previsto."},
    )
    assert reduction.status_code == 201
    change_id = reduction.json()["id"]

    again = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/approve",
        headers=auth_header(customer_token),
        json={},
    )
    assert again.status_code == 409
