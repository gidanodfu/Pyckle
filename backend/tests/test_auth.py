import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.domains.auth.service import translate_integrity_error
from app.domains.users.repository import UserRepository
from app.models.customer import CustomerProfile
from app.models.user import User
from tests.conftest import (
    CUSTOMER_EMAIL,
    PASSWORD,
    TestSession,
    auth_header,
    login,
    register_payload,
)

pytestmark = pytest.mark.asyncio

DUPLICATE_EMAIL_MESSAGE = "Este correo ya ha sido registrado, prueba con otro"


async def test_register_customer(client, geo):
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email="nuevo@test.dev", full_name="Nuevo Cliente", phone="+51922222221"
        ),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "nuevo@test.dev"
    assert body["roles"][0]["name"] == "customer"
    assert body["phone"] == "+51922222221"
    assert "hashed_password" not in body


async def test_register_duplicate_email(client, geo):
    payload = register_payload(
        geo, email="dup@test.dev", full_name="Duplicado", phone="+51922222222"
    )
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == DUPLICATE_EMAIL_MESSAGE
    assert response.json()["code"] == "email_already_registered"


async def test_register_duplicate_email_race_is_translated(client, geo, monkeypatch):
    """Simula una carrera: el lookup previo no ve el duplicado, lo frena la DB."""
    email = "race.email@test.dev"
    original = register_payload(geo, email=email, phone="+51922222231")
    assert (await client.post("/api/v1/auth/register", json=original)).status_code == 201

    async def miss_email(self, value):
        return None

    monkeypatch.setattr(UserRepository, "get_by_email", miss_email)

    raced = register_payload(geo, email=email, phone="+51922222232")
    response = await client.post("/api/v1/auth/register", json=raced)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "email_already_registered"

    async with TestSession() as session:
        users = (
            (await session.execute(select(User).where(func.lower(User.email) == email)))
            .scalars()
            .all()
        )
        profiles = (await session.execute(select(func.count(CustomerProfile.id)))).scalar_one()
    assert len(users) == 1, "no debe crearse un segundo usuario"
    assert profiles == 1, "no debe quedar un perfil parcial"

    # La sesión queda recuperable: un registro válido posterior funciona.
    followup = register_payload(geo, email="despues@test.dev", phone="+51922222233")
    assert (await client.post("/api/v1/auth/register", json=followup)).status_code == 201


async def test_register_duplicate_phone_race_is_translated(client, geo, monkeypatch):
    phone = "+51922222241"
    original = register_payload(geo, email="race.phone@test.dev", phone=phone)
    assert (await client.post("/api/v1/auth/register", json=original)).status_code == 201

    async def miss_phone(self, value):
        return None

    monkeypatch.setattr(UserRepository, "get_by_phone", miss_phone)

    raced = register_payload(geo, email="otro.phone@test.dev", phone=phone)
    response = await client.post("/api/v1/auth/register", json=raced)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "phone_already_registered"

    async with TestSession() as session:
        created = (
            await session.execute(
                select(func.count(User.id)).where(User.email == "otro.phone@test.dev")
            )
        ).scalar_one()
    assert created == 0


class _UniqueViolation:
    def __init__(self, constraint_name: str) -> None:
        self.constraint_name = constraint_name


def _integrity_error(constraint_name: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, _UniqueViolation(constraint_name))


async def test_translate_integrity_error_maps_real_constraints():
    assert (
        translate_integrity_error(_integrity_error("ix_users_email")).code
        == "email_already_registered"
    )
    assert (
        translate_integrity_error(_integrity_error("ix_users_phone_normalized")).code
        == "phone_already_registered"
    )
    assert (
        translate_integrity_error(_integrity_error("uq_oauth_accounts_provider_user")).code
        == "oauth_account_already_linked"
    )
    # Cualquier otra violación NO se interpreta como correo duplicado.
    assert translate_integrity_error(_integrity_error("otra_constraint")).code == "conflict"


async def test_register_rejects_short_password(client, geo):
    payload = register_payload(geo, email="x@test.dev", phone="+51922222223")
    payload["password"] = "123"
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


async def test_register_requires_phone_and_location(client, geo):
    without_phone = register_payload(geo, email="sin.phone@test.dev", phone="")
    without_phone.pop("phone")
    assert (await client.post("/api/v1/auth/register", json=without_phone)).status_code == 422

    without_location = {
        "email": "sin.geo@test.dev",
        "password": PASSWORD,
        "full_name": "Sin Ubicación",
        "phone": "+51922222224",
        "role": "customer",
    }
    assert (await client.post("/api/v1/auth/register", json=without_location)).status_code == 422


async def test_login_wrong_password(client, customer_token):
    response = await client.post(
        "/api/v1/auth/login", json={"email": CUSTOMER_EMAIL, "password": "incorrecta123"}
    )
    assert response.status_code == 401


async def test_me_requires_token(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_me_returns_roles_and_permissions(client, customer_token):
    response = await client.get("/api/v1/users/me", headers=auth_header(customer_token))
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == CUSTOMER_EMAIL
    assert "repair_request:create" in body["permissions"]


async def test_refresh_token_rotation(client, customer_token):
    tokens = await login(client, CUSTOMER_EMAIL, PASSWORD)
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]

    replay = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay.status_code == 401


async def test_change_password(client, customer_token):
    response = await client.post(
        "/api/v1/users/me/change-password",
        headers=auth_header(customer_token),
        json={"current_password": PASSWORD, "new_password": "nuevaClave123"},
    )
    assert response.status_code == 200
    tokens = await login(client, CUSTOMER_EMAIL, "nuevaClave123")
    assert tokens["access_token"]

    wrong = await client.post(
        "/api/v1/users/me/change-password",
        headers=auth_header(tokens["access_token"]),
        json={"current_password": "mala", "new_password": "otraClave123"},
    )
    assert wrong.status_code == 400
