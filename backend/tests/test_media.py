import pytest

from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f6a0000000049454e44ae426082"
)


async def _create_request(client, token: str) -> str:
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(token),
        json={
            "title": "Solicitud con imágenes",
            "description": "Prueba del flujo completo de imágenes y media.",
            "modality": "workshop",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_upload_persists_key_and_serves_image(client, customer_token):
    request_id = await _create_request(client, customer_token)
    upload = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(customer_token),
        files={"file": ("foto.png", PNG_1PX, "image/png")},
    )
    assert upload.status_code == 200, upload.text
    image = upload.json()["images"][0]
    assert image["url"].startswith("/api/v1/media/requests/")
    assert request_id in image["url"]

    served = await client.get(image["url"])
    assert served.status_code == 200
    assert served.content == PNG_1PX
    assert served.headers["content-type"].startswith("image/png")
    assert "max-age" in served.headers.get("cache-control", "")


async def test_media_requires_valid_signature(client):
    from app.core.paths import sign_media_url

    anonymous = await client.get("/api/v1/media/requests/00000000/unknown.png")
    assert anonymous.status_code == 401

    traversal = await client.get("/api/v1/media/%2e%2e%2f%2e%2e%2fetc%2fpasswd")
    assert traversal.status_code in {400, 401, 404}

    expired = await client.get(sign_media_url("requests/00000000/unknown.png", ttl=-1))
    assert expired.status_code == 401

    valid = sign_media_url("requests/00000000/unknown.png")
    tampered = valid.rsplit("s=", 1)[0] + "s=deadbeef"
    assert (await client.get(tampered)).status_code == 401

    signed_missing = await client.get(sign_media_url("requests/00000000/unknown.png"))
    assert signed_missing.status_code == 404


async def test_media_validates_magic_bytes_and_size(client, customer_token):
    request_id = await _create_request(client, customer_token)
    mismatch = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(customer_token),
        files={"file": ("foto.jpg", PNG_1PX, "image/jpeg")},
    )
    assert mismatch.status_code == 400

    oversized = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(customer_token),
        files={
            "file": ("grande.png", b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024), "image/png")
        },
    )
    assert oversized.status_code == 400


async def test_image_upload_requires_ownership(client, customer_token, geo):
    from tests.conftest import PASSWORD, login, register_payload

    request_id = await _create_request(client, customer_token)
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="media.otro@test.dev", phone="+51920202020"),
    )
    assert response.status_code == 201
    intruder = (await login(client, "media.otro@test.dev", PASSWORD))["access_token"]
    forbidden = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(intruder),
        files={"file": ("foto.png", PNG_1PX, "image/png")},
    )
    assert forbidden.status_code == 403


async def test_max_images_per_request(client, customer_token):
    request_id = await _create_request(client, customer_token)
    for index in range(6):
        response = await client.post(
            f"/api/v1/repair-requests/{request_id}/images",
            headers=auth_header(customer_token),
            files={"file": (f"foto{index}.png", PNG_1PX, "image/png")},
        )
        assert response.status_code == 200, response.text
    extra = await client.post(
        f"/api/v1/repair-requests/{request_id}/images",
        headers=auth_header(customer_token),
        files={"file": ("extra.png", PNG_1PX, "image/png")},
    )
    assert extra.status_code == 400
