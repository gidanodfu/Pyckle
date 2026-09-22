import pytest

from tests.conftest import (
    PASSWORD,
    TestSession,
    auth_header,
    district_by_code,
    geo_payload,
    login,
    register_payload,
)

pytestmark = pytest.mark.asyncio

JLO = "140105"
CHICLAYO = "140101"
MIRAFLORES_LIMA = "150122"
SAN_ISIDRO = "150131"


async def _geo_for(code: str) -> dict[str, str]:
    async with TestSession() as db_session:
        return geo_payload(await district_by_code(db_session, code))


async def _register_technician(client, email: str, phone: str, code: str) -> tuple[str, str]:
    geo = await _geo_for(code)
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email=email, role="technician", phone=phone, full_name="Técnico Zona"
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    specialty_id = (await client.get("/api/v1/specialties")).json()[0]["id"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    return token, specialty_id


async def _register_customer(client, email: str, phone: str, code: str) -> str:
    geo = await _geo_for(code)
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email=email, role="customer", phone=phone, full_name="Cliente Zona"
        ),
    )
    assert response.status_code == 201, response.text
    return (await login(client, email, PASSWORD))["access_token"]


async def _create_request(client, token: str, specialty_id: str, code: str, title: str) -> str:
    geo = await _geo_for(code)
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(token),
        json={
            "title": title,
            "description": "Solicitud de prueba para filtros por zona geográfica.",
            "specialty_id": specialty_id,
            "modality": "home",
            "address": "Av. Zona 123",
            **geo,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _technician_names(client, token: str | None = None, **params) -> tuple[list[str], dict]:
    query = "&".join(f"{key}={value}" for key, value in params.items())
    url = f"/api/v1/technicians?limit=50{('&' + query) if query else ''}"
    headers = auth_header(token) if token else {}
    response = await client.get(url, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    return [item["full_name"] for item in body["items"]], body


async def test_customer_sees_only_technicians_in_district(client):
    customer_token = await _register_customer(client, "zone.customer@test.dev", "+51977777771", JLO)
    await _register_technician(client, "zone.jlo@test.dev", "+51977777772", JLO)
    await _register_technician(client, "zone.lima@test.dev", "+51977777773", MIRAFLORES_LIMA)

    names, body = await _technician_names(client, customer_token)
    assert names == ["Técnico Zona"]
    assert body["scope"] == "district"
    assert body["expanded"] is False

    public_names, _ = await _technician_names(client, None)
    assert len(public_names) == 2


async def test_customer_fallback_to_province(client):
    customer_token = await _register_customer(
        client, "zone.chiclayo@test.dev", "+51977777774", CHICLAYO
    )
    await _register_technician(client, "zone.jlo2@test.dev", "+51977777775", JLO)
    await _register_technician(client, "zone.lima2@test.dev", "+51977777776", MIRAFLORES_LIMA)

    names, body = await _technician_names(client, customer_token)
    assert names == ["Técnico Zona"]
    assert body["scope"] == "province"
    assert body["expanded"] is True


async def test_technician_sees_only_requests_in_zone(client):
    technician_token, specialty_id = await _register_technician(
        client, "zone.tech@test.dev", "+51977777777", JLO
    )
    customer_jlo = await _register_customer(client, "zone.cust.jlo@test.dev", "+51977777778", JLO)
    customer_lima = await _register_customer(
        client, "zone.cust.lima@test.dev", "+51977777779", SAN_ISIDRO
    )

    local_id = await _create_request(
        client, customer_jlo, specialty_id, JLO, "Solicitud en mi distrito"
    )
    await _create_request(
        client, customer_lima, specialty_id, SAN_ISIDRO, "Solicitud fuera de zona"
    )

    response = await client.get(
        "/api/v1/repair-requests/available?limit=50",
        headers=auth_header(technician_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [local_id]
    assert body["scope"] == "district"
    assert body["expanded"] is False


async def test_technician_fallback_to_province_requests(client):
    technician_token, specialty_id = await _register_technician(
        client, "zone.tech2@test.dev", "+51977777780", JLO
    )
    customer_chiclayo = await _register_customer(
        client, "zone.cust.chic@test.dev", "+51977777781", CHICLAYO
    )
    request_id = await _create_request(
        client, customer_chiclayo, specialty_id, CHICLAYO, "Solicitud de la provincia"
    )

    response = await client.get(
        "/api/v1/repair-requests/available?limit=50",
        headers=auth_header(technician_token),
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == request_id
    assert body["scope"] == "province"
    assert body["expanded"] is True
