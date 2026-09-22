import pytest

from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f6a0000000049454e44ae426082"
)


async def test_create_and_list_request(client, customer_token, technician_ready):
    _, specialty_id = technician_ready
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Pantalla rota de celular",
            "description": "El celular se cayo y la pantalla quedo con lineas.",
            "specialty_id": specialty_id,
            "modality": "workshop",
            "budget_min": 50,
            "budget_max": 200,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "open"
    assert body["images"] == []

    listing = await client.get("/api/v1/repair-requests", headers=auth_header(customer_token))
    assert any(item["id"] == body["id"] for item in listing.json()["items"])


async def test_invalid_budget_range(client, customer_token):
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Presupuesto invalido",
            "description": "El minimo no puede superar al maximo.",
            "budget_min": 500,
            "budget_max": 100,
        },
    )
    assert response.status_code == 400


async def test_technician_sees_available(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Teclado no responde",
            "description": "Varias teclas dejaron de funcionar de repente.",
            "specialty_id": specialty_id,
        },
    )
    response = await client.get(
        "/api/v1/repair-requests/available", headers=auth_header(technician_token)
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1


async def test_upload_valid_and_invalid_image(client, customer_token):
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={"title": "Imagen de prueba", "description": "Solicitud para probar subidas."},
    )
    request_id = response.json()["id"]

    invalid = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(customer_token),
        files={"file": ("nota.txt", b"no soy una imagen", "text/plain")},
    )
    assert invalid.status_code == 400

    valid = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(customer_token),
        files={"file": ("foto.png", PNG_1PX, "image/png")},
    )
    assert valid.status_code == 200, valid.text
    assert len(valid.json()["images"]) == 1
    assert valid.json()["images"][0]["content_type"] == "image/png"
