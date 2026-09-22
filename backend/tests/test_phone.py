import pytest

from app.core.phone import normalize_phone
from tests.conftest import auth_header, login, register_payload

CANONICAL = "+51999123456"


@pytest.mark.parametrize(
    "raw",
    [
        "999123456",
        "999 123 456",
        "999-123-456",
        "+51999123456",
        "+51 999 123 456",
        "+51-999-123-456",
        "0051999123456",
        "(+51) 999 123 456",
    ],
)
def test_normalize_phone_equivalent_formats(raw):
    assert normalize_phone(raw) == CANONICAL


@pytest.mark.parametrize(
    "raw",
    [
        "123456789",
        "899123456",
        "99912345",
        "9991234567",
        "abc",
        "51",
        None,
        "",
    ],
)
def test_normalize_phone_optional_or_invalid(raw):
    if raw is None or raw.strip() == "":
        assert normalize_phone(raw) is None
    else:
        with pytest.raises(ValueError):
            normalize_phone(raw)


async def test_register_requires_valid_phone(client, geo):
    payload = register_payload(geo, email="mal.phone@test.dev", phone="999 123")
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "celular peruano" in str(response.json()["details"])


async def test_duplicate_phone_detected_across_formats(client, geo):
    first = register_payload(geo, email="phone1@test.dev", phone="+51 999 123 456")
    assert (await client.post("/api/v1/auth/register", json=first)).status_code == 201

    second = register_payload(geo, email="phone2@test.dev", phone="999-123-456")
    response = await client.post("/api/v1/auth/register", json=second)
    assert response.status_code == 409
    assert "teléfono" in response.json()["detail"]

    third = register_payload(geo, email="phone3@test.dev", phone="+51999123456")
    assert (await client.post("/api/v1/auth/register", json=third)).status_code == 409


async def test_update_phone_normalizes_and_blocks_duplicates(client, geo):
    first = register_payload(geo, email="upd1@test.dev", phone="+51955555551")
    second = register_payload(geo, email="upd2@test.dev", phone="+51955555552")
    assert (await client.post("/api/v1/auth/register", json=first)).status_code == 201
    assert (await client.post("/api/v1/auth/register", json=second)).status_code == 201

    token = (await login(client, "upd2@test.dev", "password12345"))["access_token"]
    ok = await client.patch(
        "/api/v1/users/me",
        headers=auth_header(token),
        json={"phone": "955 555 553"},
    )
    assert ok.status_code == 200
    assert ok.json()["phone"] == "+51955555553"

    duplicated = await client.patch(
        "/api/v1/users/me",
        headers=auth_header(token),
        json={"phone": "+51 955 555 551"},
    )
    assert duplicated.status_code == 409
