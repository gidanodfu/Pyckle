import pytest
from sqlalchemy import select

from app.models.user import User
from tests.conftest import TestSession, register_payload

pytestmark = pytest.mark.asyncio

EMAIL = "terms@test.dev"
PHONE = "+51950505050"


async def test_register_requires_accepting_terms(client, geo):
    payload = register_payload(geo, email=EMAIL, phone=PHONE)
    payload["accept_terms"] = False
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "Términos" in str(response.json()["details"])


async def test_register_without_terms_field_is_rejected(client, geo):
    payload = register_payload(geo, email="terms2@test.dev", phone="+51950505051")
    payload.pop("accept_terms")
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 422


async def test_acceptance_is_persisted_with_timestamp(client, geo):
    payload = register_payload(geo, email=EMAIL, phone=PHONE)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text

    async with TestSession() as session:
        user = (await session.execute(select(User).where(User.email == EMAIL))).scalar_one()
        assert user.terms_accepted_at is not None
