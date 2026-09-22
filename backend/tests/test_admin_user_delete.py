"""Borrado administrativo de usuarios: huella operativa y cascadas.

Las tablas operativas referencian ``users`` con ON DELETE CASCADE. El borrado
duro solo debe permitirse cuando el usuario no participa en ningún registro
operativo; en cualquier otro caso se devuelve 409 y se exige desactivar.
"""

import uuid

import pytest

from tests.conftest import (
    PASSWORD,
    auth_header,
    register_payload,
    run_flow,
)

pytestmark = pytest.mark.asyncio


async def _create_request(client, token: str, specialty_id: str | None = None) -> str:
    payload = {
        "title": "Solicitud sin orden para borrado",
        "description": "Solicitud creada para validar el borrado administrativo.",
        "modality": "home",
    }
    if specialty_id is not None:
        payload["specialty_id"] = specialty_id
    response = await client.post(
        "/api/v1/repair-requests", headers=auth_header(token), json=payload
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _user_id(client, token: str) -> str:
    response = await client.get("/api/v1/users/me", headers=auth_header(token))
    assert response.status_code == 200, response.text
    return response.json()["user"]["id"]


async def test_delete_customer_with_request_without_order_is_blocked(
    client, customer_token, admin_token
):
    """Un cliente con solicitudes pero sin orden no se destruye en cascada."""
    request_id = await _create_request(client, customer_token)
    customer_id = await _user_id(client, customer_token)

    response = await client.delete(
        f"/api/v1/admin/users/{customer_id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 409
    assert "desactiva" in response.json()["detail"].lower()

    # El usuario y su solicitud siguen existiendo.
    still_there = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(customer_token)
    )
    assert still_there.status_code == 200


async def test_delete_technician_with_quotation_without_order_is_blocked(
    client, customer_token, technician_ready, admin_token
):
    """Una cotización pendiente de un tercero no se destruye al borrar al técnico."""
    technician_token, specialty_id = technician_ready
    request_id = await _create_request(client, customer_token, specialty_id)
    quote = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician_token),
        json={
            "request_id": request_id,
            "price": 120,
            "preliminary_diagnosis": "Diagnóstico preliminar válido.",
        },
    )
    assert quote.status_code == 201, quote.text
    technician_id = await _user_id(client, technician_token)

    response = await client.delete(
        f"/api/v1/admin/users/{technician_id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 409

    listed = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(customer_token)
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


async def test_delete_customer_with_order_is_blocked(
    client, customer_token, technician_ready, admin_token
):
    technician_token, specialty_id = technician_ready
    await run_flow(client, customer_token, technician_token, specialty_id)
    customer_id = await _user_id(client, customer_token)

    response = await client.delete(
        f"/api/v1/admin/users/{customer_id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 409


async def test_delete_user_without_operational_footprint_succeeds(client, geo, admin_token):
    email = "delete.me@test.dev"
    registered = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email=email, phone="+51944444441"),
    )
    assert registered.status_code == 201, registered.text
    user_id = registered.json()["id"]

    response = await client.delete(
        f"/api/v1/admin/users/{user_id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 200

    # Ya no puede iniciar sesión: la cuenta dejó de existir.
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert login_response.status_code == 401


async def test_admin_cannot_delete_self(client, admin_token):
    admin_id = await _user_id(client, admin_token)
    response = await client.delete(
        f"/api/v1/admin/users/{admin_id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 409


async def test_non_admin_cannot_delete_users(client, customer_token):
    response = await client.delete(
        f"/api/v1/admin/users/{uuid.uuid4()}", headers=auth_header(customer_token)
    )
    assert response.status_code == 403
