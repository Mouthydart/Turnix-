"""Tests de los límites de plan (freemium vs pro).

Comprueban que los límites configurados se aplican al crear servicios,
empleados, reservas y al usar la lista de espera, devolviendo 402.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core import plans
from app.core.config import settings
from app.db.repositories import booking_repository
from app.models import Booking, BookingStatus, PlanName
from app.schemas.booking import BookingCreate
from app.schemas.staff import StaffCreate
from app.schemas.waitlist import WaitlistCreate
from app.services import booking as booking_service
from app.services import service as service_service
from app.services import staff as staff_service
from app.services import waitlist as waitlist_service
from tests.factories import at, make_business, make_owner, make_service, make_user, next_open_day

FREEMIUM = settings.FREEMIUM_MAX_SERVICES
FREEMIUM_EMPLOYEES = settings.FREEMIUM_MAX_EMPLOYEES


def test_limits_for_freemium_and_pro():
    freemium = plans.limits_for(PlanName.FREEMIUM)
    pro = plans.limits_for(PlanName.PRO)

    assert freemium.max_services == settings.FREEMIUM_MAX_SERVICES
    assert freemium.max_employees == settings.FREEMIUM_MAX_EMPLOYEES
    assert freemium.waitlist_enabled is False
    assert pro.max_services == settings.PRO_MAX_SERVICES
    assert pro.max_employees == settings.PRO_MAX_EMPLOYEES
    assert pro.waitlist_enabled is True


async def test_freemium_service_limit_is_enforced():
    owner = await make_owner()
    business = await make_business(owner)  # freemium

    for index in range(FREEMIUM):
        await make_service(owner, business, name=f"Servicio {index}")

    with pytest.raises(HTTPException) as exc:
        await make_service(owner, business, name="Uno de más")
    assert exc.value.status_code == 402
    assert "Actualiza tu plan" in exc.value.detail


async def test_pro_plan_allows_more_services():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")

    for index in range(FREEMIUM + 3):
        await make_service(owner, business, name=f"Servicio {index}")

    assert await service_service.list_services(owner, str(business.id))
    assert len(await service_service.list_services(owner, str(business.id))) == FREEMIUM + 3


async def test_freemium_staff_limit_is_enforced():
    owner = await make_owner()
    business = await make_business(owner)

    for index in range(FREEMIUM_EMPLOYEES):
        await staff_service.create_staff(
            owner, str(business.id), StaffCreate(display_name=f"Empleado {index}")
        )

    with pytest.raises(HTTPException) as exc:
        await staff_service.create_staff(
            owner, str(business.id), StaffCreate(display_name="Uno de más")
        )
    assert exc.value.status_code == 402


async def test_pro_plan_allows_more_staff():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")

    for index in range(FREEMIUM_EMPLOYEES + 3):
        await staff_service.create_staff(
            owner, str(business.id), StaffCreate(display_name=f"Empleado {index}")
        )

    assert len(await staff_service.list_staff(owner, str(business.id))) == FREEMIUM_EMPLOYEES + 3


async def test_freemium_waitlist_is_disabled():
    owner = await make_owner()
    business = await make_business(owner)  # freemium: waitlist off

    with pytest.raises(HTTPException) as exc:
        await waitlist_service.join_waitlist(
            str(business.id), WaitlistCreate(customer_name="X")
        )
    assert exc.value.status_code == 402


async def test_pro_waitlist_is_enabled():
    owner = await make_owner()
    business = await make_business(owner, plan="pro")

    entry = await waitlist_service.join_waitlist(
        str(business.id), WaitlistCreate(customer_name="X")
    )
    assert entry.customer_name == "X"


async def test_booking_monthly_limit_is_enforced(monkeypatch):
    monkeypatch.setattr(settings, "FREEMIUM_MAX_BOOKINGS_PER_MONTH", 0)
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, duration_minutes=60)
    staff_ = await staff_service.create_staff(
        owner, str(business.id), StaffCreate(display_name="Luis", services=[service.id])
    )
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await booking_service.create_booking(
            customer,
            str(business.id),
            BookingCreate(service_id=service.id, staff_id=staff_.id, start_at=at(day, 10, 0)),
        )
    assert exc.value.status_code == 402


async def test_count_bookings_this_month():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)
    staff_ = await staff_service.create_staff(
        owner, str(business.id), StaffCreate(display_name="Luis", services=[service.id])
    )
    now = datetime.now(UTC)

    # Dos reservas dentro del mes actual.
    for offset in range(2):
        start = now + timedelta(hours=offset + 1)
        await booking_repository.insert(
            Booking(
                business_id=business.id,
                staff_id=staff_.id,
                service_id=service.id,
                customer_id=owner.id,
                start_at=start,
                end_at=start + timedelta(hours=1),
                status=BookingStatus.PENDING,
                price=service.price,
                currency=business.currency,
            )
        )

    assert await booking_service._count_bookings_this_month(business.id) == 2
