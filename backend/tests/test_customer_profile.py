import pytest

from tests.conftest import auth_header, complete_order, drive_order, run_flow

pytestmark = pytest.mark.asyncio


async def test_authorized_technician_sees_customer_public_profile(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)

    me = await client.get("/api/v1/users/me", headers=auth_header(customer_token))
    created_at = me.json()["user"]["created_at"]

    profile = await client.get(
        f"/api/v1/orders/{order_id}/customer-profile",
        headers=auth_header(technician_token),
    )
    assert profile.status_code == 200, profile.text
    body = profile.json()
    assert body["full_name"] == "Usuario customer"
    assert body["member_since"] == created_at or body["member_since"].startswith(created_at[:16])
    assert body["completed_repairs"] == 0
    assert body["district_name"] == "José Leonardo Ortiz"
    assert body["province_name"] == "Chiclayo"
    assert body["department_name"] == "Lambayeque"
    assert "address" not in body

    # Tras completar y calificar, el contador refleja solo ordenes completadas.
    await drive_order(client, technician_token, order_id, "ready")
    await complete_order(client, technician_token, order_id)
    updated = await client.get(
        f"/api/v1/orders/{order_id}/customer-profile",
        headers=auth_header(technician_token),
    )
    assert updated.json()["completed_repairs"] == 1


async def test_customer_profile_requires_authorization(
    client, customer_token, technician_ready, geo
):
    from tests.conftest import PASSWORD, login, register_payload

    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)

    # Otro cliente no puede consultar el perfil.
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="perfil.otro@test.dev", phone="+51999999991"),
    )
    assert response.status_code == 201
    other_customer = (await login(client, "perfil.otro@test.dev", PASSWORD))["access_token"]
    forbidden = await client.get(
        f"/api/v1/orders/{order_id}/customer-profile",
        headers=auth_header(other_customer),
    )
    assert forbidden.status_code == 403

    # Un tecnico no asignado tampoco.
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo,
            email="perfil.tech@test.dev",
            role="technician",
            phone="+51999999992",
        ),
    )
    assert response.status_code == 201
    other_tech = (await login(client, "perfil.tech@test.dev", PASSWORD))["access_token"]
    forbidden_tech = await client.get(
        f"/api/v1/orders/{order_id}/customer-profile",
        headers=auth_header(other_tech),
    )
    assert forbidden_tech.status_code == 403

    missing = await client.get(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/customer-profile",
        headers=auth_header(technician_token),
    )
    assert missing.status_code == 404
