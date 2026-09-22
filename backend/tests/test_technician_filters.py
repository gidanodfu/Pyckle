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

# Lima / Lima / Miraflores y Lambayeque / Chiclayo / José Leonardo Ortiz.
LIMA = "150122"
JLO = "140105"


async def _geo_for(code: str) -> dict[str, str]:
    async with TestSession() as db_session:
        return geo_payload(await district_by_code(db_session, code))


async def _register_technician(client, email: str, phone: str, code: str, specialty_id: str) -> str:
    geo = await _geo_for(code)
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email=email, role="technician", phone=phone),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    patched = await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    assert patched.status_code == 200, patched.text
    return token


async def _technician_id(client, token: str) -> str:
    response = await client.get("/api/v1/technicians/me", headers=auth_header(token))
    return response.json()["id"]


async def _verify(client, admin_token: str, technician_id: str, verified: bool = True) -> None:
    response = await client.patch(
        f"/api/v1/admin/technicians/{technician_id}/verify?verified={str(verified).lower()}",
        headers=auth_header(admin_token),
        json={},
    )
    assert response.status_code == 200, response.text


async def test_verified_only_filter_returns_only_verified_technicians(client, admin_token):
    specialties = (await client.get("/api/v1/specialties")).json()
    first = specialties[0]["id"]

    verified_token = await _register_technician(
        client, "filters.verified@test.dev", "+51966000001", LIMA, first
    )
    await _register_technician(client, "filters.unverified@test.dev", "+51966000002", LIMA, first)
    await _verify(client, admin_token, await _technician_id(client, verified_token))

    response = await client.get("/api/v1/technicians?verified_only=true&limit=50")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["is_verified"] is True

    all_response = await client.get("/api/v1/technicians?limit=50")
    assert all_response.json()["total"] == 2


async def test_location_filters_narrow_results(client):
    specialties = (await client.get("/api/v1/specialties")).json()
    first = specialties[0]["id"]
    await _register_technician(client, "filters.lima@test.dev", "+51966000003", LIMA, first)
    await _register_technician(client, "filters.jlo@test.dev", "+51966000004", JLO, first)

    lima_geo = await _geo_for(LIMA)
    by_department = await client.get(
        f"/api/v1/technicians?department_id={lima_geo['department_id']}&limit=50"
    )
    assert by_department.json()["total"] == 1

    by_full_location = await client.get(
        "/api/v1/technicians"
        f"?department_id={lima_geo['department_id']}"
        f"&province_id={lima_geo['province_id']}"
        f"&district_id={lima_geo['district_id']}&limit=50"
    )
    assert by_full_location.json()["total"] == 1
    assert by_full_location.json()["scope"] == "district"

    jlo_geo = await _geo_for(JLO)
    other = await client.get(
        "/api/v1/technicians"
        f"?department_id={jlo_geo['department_id']}"
        f"&province_id={jlo_geo['province_id']}"
        f"&district_id={jlo_geo['district_id']}&limit=50"
    )
    assert other.json()["total"] == 1
    assert other.json()["items"][0]["district_name"] == "José Leonardo Ortiz"


async def test_combined_specialty_location_and_verified_filters(client, admin_token):
    specialties = (await client.get("/api/v1/specialties")).json()
    laptops = specialties[0]["id"]
    other_specialty = specialties[1]["id"]

    matching_token = await _register_technician(
        client, "filters.match@test.dev", "+51966000005", LIMA, laptops
    )
    await _register_technician(
        client, "filters.wrong.specialty@test.dev", "+51966000006", LIMA, other_specialty
    )
    await _register_technician(client, "filters.wrong.zone@test.dev", "+51966000007", JLO, laptops)
    await _verify(client, admin_token, await _technician_id(client, matching_token))

    geo = await _geo_for(LIMA)
    response = await client.get(
        "/api/v1/technicians"
        f"?specialty_id={laptops}"
        f"&verified_only=true"
        f"&department_id={geo['department_id']}"
        f"&province_id={geo['province_id']}"
        f"&district_id={geo['district_id']}"
        "&limit=50"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["is_verified"] is True
    assert body["items"][0]["district_name"] == "Miraflores"
