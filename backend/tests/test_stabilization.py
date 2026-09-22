"""Pruebas de las correcciones de estabilización (seguridad e integridad)."""

import pytest

from tests.conftest import (
    PASSWORD,
    auth_header,
    login,
    register_payload,
    run_flow,
    verify_technician,
)

pytestmark = pytest.mark.asyncio


async def _register_verified_technician(client, geo, *, email: str, phone: str, specialty_id: str):
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email=email, role="technician", phone=phone, full_name="Técnico Verificado"
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    await verify_technician(email)
    return token


async def _create_request(client, customer_token, specialty_id) -> str:
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Solicitud de prueba de estabilidad",
            "description": "Creada para validar reglas de negocio y autorización.",
            "specialty_id": specialty_id,
            "modality": "home",
            "address": "Av. Prueba 123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_unverified_technician_cannot_quote(client, customer_token, geo):
    specialty_id = (await client.get("/api/v1/specialties")).json()[0]["id"]
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo,
            email="tech.pending@test.dev",
            role="technician",
            phone="+51933333331",
            full_name="Técnico Pendiente",
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, "tech.pending@test.dev", PASSWORD))["access_token"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )

    request_id = await _create_request(client, customer_token, specialty_id)
    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(token),
        json={
            "request_id": request_id,
            "price": 100,
            "preliminary_diagnosis": "Diagnóstico preliminar válido.",
        },
    )
    assert quotation.status_code == 403


async def test_verified_technician_can_quote(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id = await _create_request(client, customer_token, specialty_id)
    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician_token),
        json={
            "request_id": request_id,
            "price": 100,
            "preliminary_diagnosis": "Diagnóstico preliminar válido.",
        },
    )
    assert quotation.status_code == 201


async def test_technician_only_sees_own_quotation(client, customer_token, technician_ready, geo):
    technician_token, specialty_id = technician_ready
    request_id = await _create_request(client, customer_token, specialty_id)

    own = (
        await client.post(
            "/api/v1/quotations",
            headers=auth_header(technician_token),
            json={
                "request_id": request_id,
                "price": 120,
                "preliminary_diagnosis": "Cotización propia válida.",
            },
        )
    ).json()

    other_token = await _register_verified_technician(
        client, geo, email="tech.comp@test.dev", phone="+51933333332", specialty_id=specialty_id
    )
    await client.post(
        "/api/v1/quotations",
        headers=auth_header(other_token),
        json={
            "request_id": request_id,
            "price": 90,
            "preliminary_diagnosis": "Cotización de la competencia.",
        },
    )

    listed = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(technician_token)
    )
    assert listed.status_code == 200
    assert [q["id"] for q in listed.json()] == [own["id"]]

    all_view = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(customer_token)
    )
    assert len(all_view.json()) == 2


async def test_accepting_twice_is_controlled(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id = await _create_request(client, customer_token, specialty_id)
    quotation_id = (
        await client.post(
            "/api/v1/quotations",
            headers=auth_header(technician_token),
            json={
                "request_id": request_id,
                "price": 120,
                "preliminary_diagnosis": "Cotización válida para aceptar.",
            },
        )
    ).json()["id"]

    first = await client.post(
        f"/api/v1/quotations/{quotation_id}/accept",
        headers=auth_header(customer_token),
        json={},
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/v1/quotations/{quotation_id}/accept",
        headers=auth_header(customer_token),
        json={},
    )
    assert second.status_code == 400


async def test_admin_cannot_delete_user_with_orders(
    client, customer_token, technician_ready, admin_token
):
    technician_token, specialty_id = technician_ready
    await run_flow(client, customer_token, technician_token, specialty_id)

    me = (await client.get("/api/v1/users/me", headers=auth_header(customer_token))).json()
    customer_id = me["user"]["id"]

    response = await client.delete(
        f"/api/v1/admin/users/{customer_id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 409


async def test_patch_request_rejects_invalid_budget(client, customer_token):
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Solicitud con presupuesto",
            "description": "Debe rechazar un rango de presupuesto inválido.",
            "modality": "home",
            "address": "Av. Prueba 123",
            "budget_min": 100,
            "budget_max": 200,
        },
    )
    request_id = response.json()["id"]

    invalid = await client.patch(
        f"/api/v1/repair-requests/{request_id}",
        headers=auth_header(customer_token),
        json={"budget_min": 5000},
    )
    assert invalid.status_code == 400


async def test_malformed_jwt_subject_returns_401(client):
    from app.core.security import create_access_token

    token, _ = create_access_token("not-a-uuid")
    response = await client.get("/api/v1/users/me", headers=auth_header(token))
    assert response.status_code == 401


async def test_health_does_not_leak_internals(client, monkeypatch):
    class BrokenRedis:
        async def ping(self):
            raise RuntimeError("redis://user:secret@redis:6379 fallo")

    monkeypatch.setattr("app.main.get_redis", lambda: BrokenRedis())
    response = await client.get("/api/v1/health")
    assert response.status_code == 503
    assert "secret" not in response.text
    assert "detail" not in response.json()


async def test_ws_ticket_is_single_use(client, customer_token):
    from app.core.ws_tickets import consume_ws_ticket

    unauthorized = await client.post("/api/v1/ws/ticket")
    assert unauthorized.status_code == 401

    response = await client.post("/api/v1/ws/ticket", headers=auth_header(customer_token))
    assert response.status_code == 200
    data = response.json()
    assert data["ticket"]
    assert data["expires_in"] > 0

    assert await consume_ws_ticket(data["ticket"]) is not None
    assert await consume_ws_ticket(data["ticket"]) is None


async def test_orders_can_be_filtered_by_request(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)

    filtered = await client.get(
        f"/api/v1/orders?request_id={request_id}", headers=auth_header(customer_token)
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == order_id


async def test_conversations_can_be_filtered_by_request(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, _ = await run_flow(client, customer_token, technician_token, specialty_id)

    filtered = await client.get(
        f"/api/v1/conversations?request_id={request_id}", headers=auth_header(customer_token)
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["request_id"] == request_id
