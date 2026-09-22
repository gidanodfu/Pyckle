"""Ciclo de reparación: pruebas por comportamiento."""

import pytest

from tests.conftest import (
    auth_header,
    complete_order,
    drive_order,
    new_order,
    other_verified_technician,
)

pytestmark = pytest.mark.asyncio


async def test_report_download_authorization_and_content(
    client, customer_token, technician_ready, geo, admin_token
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text

    reports = await client.get(
        f"/api/v1/orders/{order_id}/reports", headers=auth_header(customer_token)
    )
    assert reports.status_code == 200
    assert len(reports.json()) == 1
    assert reports.json()[0]["version"] == 1

    for token in (customer_token, technician_token, admin_token):
        response = await client.get(f"/api/v1/orders/{order_id}/report", headers=auth_header(token))
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("application/pdf")
        assert len(response.content) > 500
        assert response.content[:5] == b"%PDF-"

    intruder = await other_verified_technician(
        client,
        geo,
        email="report.intruso@test.dev",
        phone="+51977777772",
        specialty_id=specialty_id,
    )
    denied = await client.get(f"/api/v1/orders/{order_id}/report", headers=auth_header(intruder))
    assert denied.status_code == 403


async def test_report_renders_long_cost_description(client, customer_token, technician_ready):
    """Una descripción de costo larga no debe romper la generación del informe."""
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)

    long_description = (
        "Reemplazo de la placa principal con soldadura de precisión, "
        "verificación de continuidad en todos los pines y pruebas térmicas "
        "prolongadas antes de la calibración final del equipo."
    )
    created = await client.post(
        f"/api/v1/orders/{order_id}/costs",
        headers=auth_header(technician_token),
        json={
            "kind": "part",
            "description": long_description,
            "amount": 120,
            "visible_to_customer": True,
        },
    )
    assert created.status_code == 201, created.text

    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text

    response = await client.get(
        f"/api/v1/orders/{order_id}/report", headers=auth_header(customer_token)
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content[:5] == b"%PDF-"
