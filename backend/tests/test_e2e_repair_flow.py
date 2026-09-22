"""E2E del ciclo de reparación: flujo con cambio de precio e informe, y flujo no reparable."""

import pytest

from tests.conftest import (
    TestSession,
    auth_header,
    district_by_code,
    geo_payload,
    login,
    register_payload,
    verify_technician,
)

pytestmark = pytest.mark.asyncio


async def _geo(code: str) -> dict[str, str]:
    async with TestSession() as db_session:
        return geo_payload(await district_by_code(db_session, code))


async def _setup(client):
    geo = await _geo("140105")
    specialty_id = (await client.get("/api/v1/specialties")).json()[0]["id"]

    customer_reg = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo,
            email="e2e.repair.customer@test.dev",
            phone="+51950505050",
            full_name="Elena Cliente",
            address="Av. Reparación 100",
        ),
    )
    assert customer_reg.status_code == 201, customer_reg.text
    customer = (await login(client, "e2e.repair.customer@test.dev", "password12345"))[
        "access_token"
    ]

    tech_reg = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo,
            email="e2e.repair.tech@test.dev",
            role="technician",
            phone="+51950505051",
            full_name="Mario Técnico",
        ),
    )
    assert tech_reg.status_code == 201, tech_reg.text
    technician = (await login(client, "e2e.repair.tech@test.dev", "password12345"))["access_token"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(technician),
        json={"specialty_ids": [specialty_id]},
    )
    await verify_technician("e2e.repair.tech@test.dev")
    return geo, specialty_id, customer, technician


async def _create_and_accept(client, customer, technician, specialty_id, title):
    created = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer),
        json={
            "title": title,
            "description": "Descripción del problema reportado por el cliente.",
            "specialty_id": specialty_id,
            "modality": "workshop",
        },
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]

    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician),
        json={
            "request_id": request_id,
            "price": 180,
            "preliminary_diagnosis": "Diagnóstico preliminar del equipo.",
        },
    )
    assert quotation.status_code == 201, quotation.text
    quotation_id = quotation.json()["id"]

    accepted = await client.post(
        f"/api/v1/quotations/{quotation_id}/accept",
        headers=auth_header(customer),
        json={},
    )
    assert accepted.status_code == 200, accepted.text
    return request_id, accepted.json()["id"]


async def test_e2e_repair_with_price_change_and_report(client):
    _geo_data, specialty_id, customer, technician = await _setup(client)
    request_id, order_id = await _create_and_accept(
        client, customer, technician, specialty_id, "Laptop con falla intermitente"
    )

    order = (await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(technician))).json()
    assert order["status"] == "awaiting_receipt"

    for status in ("received", "diagnosis"):
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=auth_header(technician),
            json={"status": status},
        )
        assert response.status_code == 200, response.text

    # Costo adicional: requiere aprobación del cliente y bloquea el trabajo facturable.
    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician),
        json={"new_price": 240, "reason": "Se encontró daño adicional en la placa."},
    )
    assert proposal.status_code == 201, proposal.text
    change_id = proposal.json()["id"]

    blocked = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician),
        json={"status": "in_repair"},
    )
    assert blocked.status_code == 409

    customer_notifications = (
        await client.get("/api/v1/notifications", headers=auth_header(customer))
    ).json()
    assert any(item["type"] == "price_change_requested" for item in customer_notifications)

    approve = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/approve",
        headers=auth_header(customer),
        json={},
    )
    assert approve.status_code == 200, approve.text

    for status in ("in_repair", "testing", "ready"):
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=auth_header(technician),
            json={"status": status},
        )
        assert response.status_code == 200, response.text

    completed = await client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers=auth_header(technician),
        json={
            "final_price": 240,
            "diagnosis": "Falla confirmada en la placa de carga.",
            "work_performed": "Reemplazo del componente y pruebas.",
            "tests_performed": "Encendido, carga y estabilidad.",
        },
    )
    assert completed.status_code == 200, completed.text
    body = completed.json()
    assert body["status"] == "completed"
    assert body["result"] == "repaired"
    assert float(body["final_price"]) == 240.0
    assert body["report"] is not None

    # El cliente accede al informe; un ajeno no.
    report = await client.get(f"/api/v1/orders/{order_id}/report", headers=auth_header(customer))
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("application/pdf")
    assert report.content[:5] == b"%PDF-"
    assert len(report.content) > 500

    geo = _geo_data
    stranger_reg = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="e2e.repair.stranger@test.dev", phone="+51950505052"),
    )
    assert stranger_reg.status_code == 201
    stranger = (await login(client, "e2e.repair.stranger@test.dev", "password12345"))[
        "access_token"
    ]
    denied = await client.get(f"/api/v1/orders/{order_id}/report", headers=auth_header(stranger))
    assert denied.status_code == 403

    # Historial disponible y solicitud cerrada.
    events = body["events"]
    assert any(event["new_status"] == "completed" for event in events)
    request = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(customer)
    )
    assert request.json()["status"] == "completed"

    completed_notifications = (
        await client.get("/api/v1/notifications", headers=auth_header(customer))
    ).json()
    assert any(item["type"] == "repair_completed" for item in completed_notifications)


async def test_e2e_not_repairable_flow(client):
    _geo_data, specialty_id, customer, technician = await _setup(client)
    request_id, order_id = await _create_and_accept(
        client, customer, technician, specialty_id, "Equipo con daño irreparable"
    )

    await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician),
        json={"status": "received"},
    )
    await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician),
        json={"status": "diagnosis"},
    )

    result = await client.post(
        f"/api/v1/orders/{order_id}/not-repairable",
        headers=auth_header(technician),
        json={
            "reason": "Corrosión severa que compromete la placa principal.",
            "diagnosis": "Diagnóstico técnico con evidencia de daño irreparable.",
            "recommendation": "Reemplazar el equipo.",
        },
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["status"] == "completed"
    assert body["result"] == "not_repairable"
    assert body["report"] is not None

    report = await client.get(f"/api/v1/orders/{order_id}/report", headers=auth_header(customer))
    assert report.status_code == 200
    assert report.content[:5] == b"%PDF-"

    request = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(customer)
    )
    assert request.json()["status"] == "completed"

    notifications = (
        await client.get("/api/v1/notifications", headers=auth_header(customer))
    ).json()
    assert any(item["type"] == "repair_not_repairable" for item in notifications)
