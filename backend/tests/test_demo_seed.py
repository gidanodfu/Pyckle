import pytest
from sqlalchemy import func, select

from app.db import demo_seed
from app.models.enums import RoleName
from app.models.order import Order
from app.models.repair import RepairRequest
from app.models.review import Review
from app.models.technician import Specialty, Technician, technician_specialties
from app.models.user import Role, User
from tests.conftest import TestSession

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def demo_password(monkeypatch):
    monkeypatch.setattr(demo_seed.settings, "demo_password", "demo-password-123", raising=False)
    yield


async def _run_seed() -> None:
    async with TestSession() as session:
        specialties = list(
            (await session.execute(select(Specialty).order_by(Specialty.name))).scalars().all()
        )
        await demo_seed.seed_demo(session, specialties)


async def _count_users_with_role(role_name: str) -> int:
    async with TestSession() as session:
        stmt = (
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(User.roles)
            .where(Role.name == role_name.value)
        )
        return int((await session.execute(stmt)).scalar_one())


async def test_demo_seed_creates_distributed_data_with_integrity():
    await _run_seed()

    async with TestSession() as session:
        technicians = list((await session.execute(select(Technician))).scalars().all())
        verified = [item for item in technicians if item.is_verified]
        unverified = [item for item in technicians if not item.is_verified]
        departments = {item.department_id for item in technicians if item.department_id}
        specialty_ids = set(
            (await session.execute(select(technician_specialties.c.specialty_id))).scalars().all()
        )
        orders = int((await session.execute(select(func.count(Order.id)))).scalar_one())
        reviews = int((await session.execute(select(func.count(Review.id)))).scalar_one())
        open_requests = int(
            (
                await session.execute(
                    select(func.count(RepairRequest.id)).where(RepairRequest.status == "open")
                )
            ).scalar_one()
        )
        missing_location = int(
            (
                await session.execute(
                    select(func.count(Technician.id)).where(Technician.district_id.is_(None))
                )
            ).scalar_one()
        )

    assert await _count_users_with_role(RoleName.CUSTOMER) >= 13
    assert await _count_users_with_role(RoleName.TECHNICIAN) >= 13
    assert len(technicians) >= 13
    assert len(verified) >= 6
    assert len(unverified) >= 6
    assert len(departments) >= 9
    assert len(specialty_ids) == 7
    assert orders >= len(demo_seed.DEMO_COMPLETED)
    assert reviews >= 9
    assert open_requests >= len(demo_seed.DEMO_OPEN)
    assert missing_location == 0


async def test_demo_seed_is_idempotent():
    await _run_seed()
    async with TestSession() as session:
        first = {
            "customers": await _count_users_with_role(RoleName.CUSTOMER),
            "technicians": await _count_users_with_role(RoleName.TECHNICIAN),
            "requests": int(
                (await session.execute(select(func.count(RepairRequest.id)))).scalar_one()
            ),
            "orders": int((await session.execute(select(func.count(Order.id)))).scalar_one()),
            "reviews": int((await session.execute(select(func.count(Review.id)))).scalar_one()),
        }

    await _run_seed()
    await _run_seed()

    async with TestSession() as session:
        second = {
            "customers": await _count_users_with_role(RoleName.CUSTOMER),
            "technicians": await _count_users_with_role(RoleName.TECHNICIAN),
            "requests": int(
                (await session.execute(select(func.count(RepairRequest.id)))).scalar_one()
            ),
            "orders": int((await session.execute(select(func.count(Order.id)))).scalar_one()),
            "reviews": int((await session.execute(select(func.count(Review.id)))).scalar_one()),
        }

    assert first == second
