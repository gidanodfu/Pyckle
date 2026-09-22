import pytest

from tests.conftest import auth_header, register_payload

pytestmark = pytest.mark.asyncio

LAMBAYEQUE = "Lambayeque"
CHICLAYO = "Chiclayo"
JLO = "José Leonardo Ortiz"


async def test_departments_and_hierarchy(client):
    departments = (await client.get("/api/v1/geo/departments")).json()
    assert len(departments) == 25
    lambayeque = next(item for item in departments if item["name"] == LAMBAYEQUE)

    provinces = (await client.get(f"/api/v1/geo/departments/{lambayeque['id']}/provinces")).json()
    chiclayo = next(item for item in provinces if item["name"] == CHICLAYO)
    assert chiclayo["department_id"] == lambayeque["id"]

    districts = (await client.get(f"/api/v1/geo/provinces/{chiclayo['id']}/districts")).json()
    assert JLO in [item["name"] for item in districts]
    jlo = next(item for item in districts if item["name"] == JLO)
    assert jlo["province_id"] == chiclayo["id"]
    assert jlo["department_id"] == lambayeque["id"]


async def test_geo_seed_is_complete(session):
    from sqlalchemy import func, select

    from app.models.geo import Department, District, Province

    departments = (await session.execute(select(func.count(Department.id)))).scalar_one()
    provinces = (await session.execute(select(func.count(Province.id)))).scalar_one()
    districts = (await session.execute(select(func.count(District.id)))).scalar_one()
    assert departments == 25
    assert provinces == 196
    assert districts == 1874


async def test_register_without_location_is_rejected(client):
    payload = {
        "email": "sin.ubicacion@test.dev",
        "password": "password12345",
        "full_name": "Sin Ubicación",
        "phone": "+51933333330",
        "role": "customer",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


async def test_register_rejects_invalid_hierarchy(client, geo):
    departments = (await client.get("/api/v1/geo/departments")).json()
    lima = next(item for item in departments if item["name"] == "Lima")
    payload = register_payload(geo, email="jerarquia@test.dev", phone="+51933333331")
    payload["department_id"] = lima["id"]  # provincia/distrito de Lambayeque
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "provincia" in response.json()["detail"].lower()


async def test_customer_can_update_location(client, customer_token, geo):
    response = await client.patch(
        "/api/v1/users/me/customer-profile",
        headers=auth_header(customer_token),
        json={
            "address": "Calle Nueva 456",
            **geo,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["district_name"] == JLO
    assert body["province_name"] == CHICLAYO
    assert body["department_name"] == LAMBAYEQUE
    assert body["address"] == "Calle Nueva 456"

    me = await client.get("/api/v1/users/me", headers=auth_header(customer_token))
    profile = me.json()["customer_profile"]
    assert profile["district_name"] == JLO
    assert profile["department_name"] == LAMBAYEQUE


async def test_technician_workshop_requires_address(client, technician_ready, geo):
    technician_token, _ = technician_ready

    without_address = await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(technician_token),
        json={"offers_workshop_service": True, "workshop_address": None},
    )
    assert without_address.status_code == 400
    assert "taller" in without_address.json()["detail"].lower()

    with_address = await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(technician_token),
        json={"offers_workshop_service": True, "workshop_address": "Av. Taller 456", **geo},
    )
    assert with_address.status_code == 200, with_address.text
    assert with_address.json()["workshop_address"] == "Av. Taller 456"
    assert with_address.json()["district_name"] == JLO

    disabled = await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(technician_token),
        json={"offers_workshop_service": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["offers_workshop_service"] is False


async def test_customer_update_location_invalid_relation(client, customer_token):
    departments = (await client.get("/api/v1/geo/departments")).json()
    lima = next(item for item in departments if item["name"] == "Lima")
    provinces = (await client.get(f"/api/v1/geo/departments/{lima['id']}/provinces")).json()
    lima_province = next(item for item in provinces if item["name"].strip() == "Lima")

    response = await client.patch(
        "/api/v1/users/me/customer-profile",
        headers=auth_header(customer_token),
        json={
            "department_id": lima["id"],
            "province_id": lima_province["id"],
            "district_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 400
