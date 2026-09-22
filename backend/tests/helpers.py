"""Helpers compartidos de los tests (datos, flujos y utilidades)."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.customer import CustomerProfile
from app.models.enums import RoleName
from app.models.geo import Department, District, Province
from app.models.user import Role, User
from tests.infra import PASSWORD, TestSession


async def get_district(session, department_code: str = "14", name: str = "José Leonardo Ortiz"):

    stmt = (
        select(District)
        .options(selectinload(District.province).selectinload(Province.department))
        .join(Province, District.province_id == Province.id)
        .join(Department, Province.department_id == Department.id)
        .where(Department.code == department_code, District.name == name)
    )
    return (await session.execute(stmt)).scalar_one()


async def district_by_code(session, code: str) -> District:

    stmt = (
        select(District)
        .options(selectinload(District.province).selectinload(Province.department))
        .where(District.code == code)
    )
    return (await session.execute(stmt)).scalar_one()


async def location_payload(code: str) -> dict[str, str]:
    async with TestSession() as db_session:
        return geo_payload(await district_by_code(db_session, code))


def geo_payload(district: District) -> dict[str, str]:
    return {
        "department_id": str(district.department_id),
        "province_id": str(district.province_id),
        "district_id": str(district.id),
    }


def register_payload(
    geo: dict[str, str],
    *,
    email: str,
    role: str = "customer",
    phone: str = "+51911111111",
    full_name: str = "Usuario de Prueba",
    password: str = PASSWORD,
    **extra,
) -> dict:
    return {
        "email": email,
        "password": password,
        "full_name": full_name,
        "phone": phone,
        "role": role,
        "accept_terms": True,
        **geo,
        **extra,
    }


async def create_user(email: str, password: str, role_name: RoleName) -> User:

    async with TestSession() as db_session:
        role = (
            await db_session.execute(select(Role).where(Role.name == role_name.value))
        ).scalar_one()
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=f"Usuario {role_name.value}",
        )
        user.roles.append(role)
        db_session.add(user)
        await db_session.flush()
        if role_name == RoleName.CUSTOMER:
            district = await get_district(db_session)
            db_session.add(
                CustomerProfile(
                    user_id=user.id,
                    address="Av. Prueba 123",
                    district=district.name,
                    city=district.province.department.name,
                    department_id=district.department_id,
                    province_id=district.province_id,
                    district_id=district.id,
                )
            )
        await db_session.commit()
        await db_session.refresh(user)
        return user


async def verify_technician(email: str) -> None:
    """Marca al técnico como verificado (regla previa a poder cotizar)."""

    from app.models.technician import Technician
    from app.models.user import User as UserModel

    async with TestSession() as db_session:
        user = (
            await db_session.execute(select(UserModel).where(UserModel.email == email))
        ).scalar_one()
        technician = (
            await db_session.execute(select(Technician).where(Technician.user_id == user.id))
        ).scalar_one()
        technician.is_verified = True
        await db_session.commit()


async def login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def run_flow(
    client: AsyncClient, customer_token: str, technician_token: str, specialty_id: str
) -> tuple[str, str, str]:
    """Solicitud -> cotizacion -> aceptar -> orden. Devuelve (request, quotation, order)."""
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Falla de prueba en laptop",
            "description": "La laptop se apaga sola despues de unos minutos de uso.",
            "specialty_id": specialty_id,
            "modality": "home",
        },
    )
    assert response.status_code == 201, response.text
    request_id = response.json()["id"]

    response = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician_token),
        json={
            "request_id": request_id,
            "price": 150,
            "preliminary_diagnosis": "Sobrecalentamiento, requiere mantenimiento.",
            "estimated_days": 1,
        },
    )
    assert response.status_code == 201, response.text
    quotation_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/quotations/{quotation_id}/accept",
        headers=auth_header(customer_token),
        json={},
    )
    assert response.status_code == 200, response.text
    order_id = response.json()["id"]
    return request_id, quotation_id, order_id


async def drive_order(client, technician_token: str, order_id: str, target: str) -> None:
    """Lleva una orden por las transiciones técnicas válidas hasta ``target``."""
    paths = {
        "received": ["received"],
        "diagnosis": ["received", "diagnosis"],
        "waiting_customer": ["received", "diagnosis", "waiting_customer"],
        "waiting_part": ["received", "diagnosis", "waiting_part"],
        "in_repair": ["received", "diagnosis", "in_repair"],
        "testing": ["received", "diagnosis", "in_repair", "testing"],
        "ready": ["received", "diagnosis", "in_repair", "testing", "ready"],
    }
    for status in paths[target]:
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=auth_header(technician_token),
            json={"status": status},
        )
        assert response.status_code == 200, response.text


async def complete_order(client, technician_token: str, order_id: str, **extra):
    """Completa una reparación generando el informe obligatorio."""
    payload = {
        "diagnosis": "Diagnóstico técnico de prueba con suficiente detalle.",
        "work_performed": "Trabajo realizado de prueba.",
        "tests_performed": "Pruebas realizadas de prueba.",
    }
    payload.update(extra)
    return await client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers=auth_header(technician_token),
        json=payload,
    )


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def other_verified_technician(
    client, geo, *, email: str, phone: str, specialty_id: str
) -> str:
    """Registra un técnico ajeno, le asigna especialidad y lo verifica."""
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email=email, role="technician", phone=phone, full_name="Técnico Ajeno"
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    await verify_technician(email)
    return token


async def new_order(client, customer_token, technician_token, specialty_id):
    """Crea solicitud + cotización + aceptación; devuelve (request, quotation, order)."""
    return await run_flow(client, customer_token, technician_token, specialty_id)
