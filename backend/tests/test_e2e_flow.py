"""Flujo end-to-end del marketplace (Fase 22)."""

import pytest

from tests.conftest import (
    TestSession,
    auth_header,
    complete_order,
    district_by_code,
    drive_order,
    geo_payload,
    login,
    register_payload,
    verify_technician,
)

pytestmark = pytest.mark.asyncio

CUSTOMER_PHONE = "+51940404040"
TECH_PHONE = "+51940404041"
OTHER_PHONE = "+51940404042"
PRIVATE_ADDRESS = "Av. Balta 742, José Leonardo Ortiz"


async def _geo(code: str) -> dict[str, str]:
    async with TestSession() as db_session:
        return geo_payload(await district_by_code(db_session, code))


async def test_full_marketplace_flow(client):
    geo_jlo = await _geo("140105")
    specialty_id = (await client.get("/api/v1/specialties")).json()[0]["id"]

    # 1. Registro de cliente con teléfono, ubicación y dirección privada.
    customer_register = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo_jlo,
            email="e2e.cliente@test.dev",
            phone=CUSTOMER_PHONE,
            full_name="Carlos Pérez",
            address=PRIVATE_ADDRESS,
        ),
    )
    assert customer_register.status_code == 201, customer_register.text
    customer_id = customer_register.json()["id"]
    customer = (await login(client, "e2e.cliente@test.dev", "password12345"))["access_token"]

    # 2. Registro de técnico con ubicación y local.
    tech_register = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo_jlo,
            email="e2e.tecnico@test.dev",
            role="technician",
            phone=TECH_PHONE,
            full_name="Luis Técnico",
            offers_workshop_service=True,
            workshop_address="Av. Chiclayo 100",
        ),
    )
    assert tech_register.status_code == 201, tech_register.text
    technician = (await login(client, "e2e.tecnico@test.dev", "password12345"))["access_token"]
    assert (
        await client.patch(
            "/api/v1/technicians/me",
            headers=auth_header(technician),
            json={"specialty_ids": [specialty_id]},
        )
    ).status_code == 200
    technician_id = (
        await client.get("/api/v1/technicians/me", headers=auth_header(technician))
    ).json()["id"]
    await verify_technician("e2e.tecnico@test.dev")

    # 3. Usuario ajeno para validar privacidad.
    other_register = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo_jlo,
            email="e2e.ajeno@test.dev",
            phone=OTHER_PHONE,
            full_name="Usuario Ajeno",
        ),
    )
    assert other_register.status_code == 201, other_register.text
    other = (await login(client, "e2e.ajeno@test.dev", "password12345"))["access_token"]

    # 4. El cliente publica una solicitud a domicilio.
    created = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer),
        json={
            "title": "Laptop no enciende tras la lluvia",
            "description": "La laptop dejó de encender y necesito revisión a domicilio.",
            "specialty_id": specialty_id,
            "modality": "home",
            "address": PRIVATE_ADDRESS,
            **geo_jlo,
        },
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    assert created.json()["address"] == PRIVATE_ADDRESS

    # 5. La dirección no es visible para el técnico antes de aceptar.
    before = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(technician)
    )
    assert before.status_code == 200
    assert before.json()["address"] is None
    forbidden = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(other)
    )
    assert forbidden.status_code == 403

    # El perfil público del cliente no expone dirección (solo técnicos con orden).
    listing = await client.get("/api/v1/technicians?limit=50")
    assert all("address" not in item for item in listing.json()["items"])

    # 6. El técnico ve la solicitud porque está en su zona.
    available = await client.get(
        "/api/v1/repair-requests/available?limit=50",
        headers=auth_header(technician),
    )
    assert available.status_code == 200
    assert available.json()["total"] == 1
    assert available.json()["scope"] == "district"

    # 7. El técnico cotiza y el cliente la visualiza.
    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician),
        json={
            "request_id": request_id,
            "price": 180,
            "preliminary_diagnosis": "Posible falla en la placa de carga.",
            "estimated_days": 2,
        },
    )
    assert quotation.status_code == 201, quotation.text
    quotation_id = quotation.json()["id"]

    quotations = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(customer)
    )
    assert quotations.status_code == 200
    first = quotations.json()[0]
    assert first["technician"]["full_name"] == "Luis Técnico"
    assert first["technician_reviews"] == []

    # 8. El cliente acepta la cotización: se crea la orden y la conversación.
    accepted = await client.post(
        f"/api/v1/quotations/{quotation_id}/accept",
        headers=auth_header(customer),
        json={},
    )
    assert accepted.status_code == 200, accepted.text
    order_id = accepted.json()["id"]

    # 9. El técnico asignado obtiene la dirección; el ajeno no.
    assigned_view = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(technician))
    assert assigned_view.json()["service_address"] == PRIVATE_ADDRESS
    other_view = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(other))
    assert other_view.status_code == 403

    # 10. Chat activo: ambos pueden enviar.
    conversations = (
        await client.get("/api/v1/conversations", headers=auth_header(customer))
    ).json()
    conversation = next(item for item in conversations if item["request_id"] == request_id)
    assert conversation["status"] == "open"
    for token, body in (
        (customer, "Hola, ¿puedes venir mañana?"),
        (technician, "Sí, voy por la tarde."),
    ):
        message = await client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=auth_header(token),
            json={"body": body},
        )
        assert message.status_code == 201, message.text

    # 11. La reparación finaliza y el chat se cierra/archiva.
    await drive_order(client, technician, order_id, "ready")
    completed = await complete_order(client, technician, order_id)
    assert completed.status_code == 200, completed.text
    assert completed.json()["report"] is not None

    archived = (await client.get("/api/v1/conversations", headers=auth_header(customer))).json()
    archived_conversation = next(item for item in archived if item["request_id"] == request_id)
    assert archived_conversation["status"] == "archived"
    assert archived_conversation["closed_at"] is not None

    blocked = await client.post(
        f"/api/v1/conversations/{archived_conversation['id']}/messages",
        headers=auth_header(customer),
        json={"body": "Mensaje posterior al cierre"},
    )
    assert blocked.status_code == 409

    history = await client.get(
        f"/api/v1/conversations/{archived_conversation['id']}/messages",
        headers=auth_header(customer),
    )
    assert len(history.json()) == 2

    # 12. Reseña del cliente y perfil público del cliente para el técnico.
    review = await client.post(
        "/api/v1/reviews",
        headers=auth_header(customer),
        json={"order_id": order_id, "rating": 5, "comment": "Excelente servicio."},
    )
    assert review.status_code == 201, review.text

    profile = await client.get(
        f"/api/v1/orders/{order_id}/customer-profile",
        headers=auth_header(technician),
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["full_name"] == "Carlos Pérez"
    assert profile.json()["completed_repairs"] == 1
    assert profile.json()["district_name"] == "José Leonardo Ortiz"
    assert "address" not in profile.json()

    quotation_list = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(customer)
    )
    embedded = quotation_list.json()[0]["technician_reviews"]
    assert len(embedded) == 1
    assert embedded[0]["rating"] == 5
    assert embedded[0]["customer_name"] == "Carlos Pérez"

    # 13. Notificaciones: marcar como leídas y reactivar con una nueva.
    read_all = await client.post("/api/v1/notifications/read-all", headers=auth_header(customer))
    assert read_all.json()["unread"] == 0
    idle = await client.post("/api/v1/notifications/read-all", headers=auth_header(customer))
    assert idle.json()["updated"] == 0

    await client.post(
        f"/api/v1/conversations/{archived_conversation['id']}/messages",
        headers=auth_header(technician),
        json={"body": "No debería notificar"},
    )
    # El chat está archivado: el mensaje no se crea y no genera notificación.
    unread = await client.get("/api/v1/notifications/unread-count", headers=auth_header(customer))
    assert unread.json()["unread"] == 0

    # 14. El técnico aparece con rating actualizado en el marketplace.
    public = await client.get(f"/api/v1/technicians/{technician_id}")
    assert public.status_code == 200
    assert float(public.json()["rating_avg"]) == 5.0
    assert public.json()["rating_count"] == 1
    assert public.json()["district_name"] == "José Leonardo Ortiz"

    # El teléfono canónico se almacena en formato +51.
    me = await client.get("/api/v1/users/me", headers=auth_header(customer))
    assert me.json()["user"]["phone"] == CUSTOMER_PHONE
    assert me.json()["user"]["id"] == customer_id
