import pytest

from tests.conftest import auth_header, login, register_payload

pytestmark = pytest.mark.asyncio

ACCENTED_TEXT = (
    "Revisión de años: reseña del técnico, cotización y dirección. "
    "Contraseña segura, notificación enviada."
)


async def test_accented_registration_and_request_roundtrip(client, geo):
    payload = register_payload(
        geo,
        email="unicode@test.dev",
        phone="+51930303030",
        full_name="José Ramírez Ñopo",
    )
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["full_name"] == "José Ramírez Ñopo"
    token = (await login(client, "unicode@test.dev", "password12345"))["access_token"]

    me = await client.get("/api/v1/users/me", headers=auth_header(token))
    assert me.json()["user"]["full_name"] == "José Ramírez Ñopo"
    assert me.json()["customer_profile"]["district_name"] == "José Leonardo Ortiz"
    assert me.json()["customer_profile"]["department_name"] == "Lambayeque"

    created = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(token),
        json={
            "title": "Reparación tras años de uso",
            "description": ACCENTED_TEXT,
            "modality": "workshop",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["title"] == "Reparación tras años de uso"
    assert body["description"] == ACCENTED_TEXT

    fetched = await client.get(f"/api/v1/repair-requests/{body['id']}", headers=auth_header(token))
    assert fetched.json()["description"] == ACCENTED_TEXT


async def test_geo_names_keep_accents(client):
    departments = (await client.get("/api/v1/geo/departments")).json()
    names = {item["name"] for item in departments}
    assert {"Áncash", "Apurímac", "Huánuco", "Junín", "San Martín", "Lambayeque"} <= names
