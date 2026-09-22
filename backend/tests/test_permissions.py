import pytest

from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


async def test_customer_cannot_access_admin(client, customer_token):
    response = await client.get("/api/v1/admin/stats", headers=auth_header(customer_token))
    assert response.status_code == 403


async def test_technician_cannot_access_admin(client, technician_token):
    response = await client.get("/api/v1/admin/stats", headers=auth_header(technician_token))
    assert response.status_code == 403


async def test_customer_cannot_create_quotation(client, customer_token, technician_ready):
    _, specialty_id = technician_ready
    request = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Solicitud para permisos",
            "description": "Descripcion suficientemente larga para validar.",
            "specialty_id": specialty_id,
        },
    )
    response = await client.post(
        "/api/v1/quotations",
        headers=auth_header(customer_token),
        json={
            "request_id": request.json()["id"],
            "price": 100,
            "preliminary_diagnosis": "Diagnostico preliminar de prueba.",
        },
    )
    assert response.status_code == 403


async def test_unauthenticated_cannot_create_request(client):
    response = await client.post(
        "/api/v1/repair-requests",
        json={"title": "Sin token", "description": "No deberia pasar nunca."},
    )
    assert response.status_code == 401


async def test_customer_cannot_view_other_request(client, customer_token):
    from app.models.enums import RoleName
    from tests.conftest import PASSWORD, create_user, login

    other = await create_user("otro@test.dev", PASSWORD, RoleName.CUSTOMER)
    other_token = (await login(client, "otro@test.dev", PASSWORD))["access_token"]
    assert other.id

    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={"title": "Privada del cliente", "description": "Solo yo deberia verla."},
    )
    request_id = response.json()["id"]

    forbidden = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(other_token)
    )
    assert forbidden.status_code == 403


async def test_admin_can_list_users(client, admin_token):
    response = await client.get("/api/v1/admin/users", headers=auth_header(admin_token))
    assert response.status_code == 200
    assert "items" in response.json()
