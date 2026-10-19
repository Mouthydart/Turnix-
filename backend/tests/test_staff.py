"""Tests del CRUD de empleados: validación de servicios, dedupe y cuenta vinculada."""

import pytest
from fastapi import HTTPException

from app.schemas.staff import StaffCreate, StaffUpdate
from app.services import staff as staff_service
from tests.factories import (
    make_business,
    make_owner,
    make_service,
    make_staff,
    make_user,
)


async def test_create_staff_with_services():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)

    staff = await make_staff(owner, business, display_name="Luis", services=[str(service.id)])

    assert staff.display_name == "Luis"
    assert staff.services == [service.id]


async def test_staff_services_are_deduplicated():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)

    staff = await make_staff(
        owner, business, services=[str(service.id), str(service.id), str(service.id)]
    )

    assert staff.services == [service.id]


async def test_staff_with_service_from_other_business_is_rejected():
    owner = await make_owner()
    business_a = await make_business(owner, name="A")
    business_b = await make_business(owner, name="B")
    foreign_service = await make_service(owner, business_b)

    with pytest.raises(HTTPException) as exc:
        await make_staff(owner, business_a, services=[str(foreign_service.id)])
    assert exc.value.status_code == 422


async def test_staff_with_unknown_user_is_rejected():
    owner = await make_owner()
    business = await make_business(owner)

    with pytest.raises(HTTPException) as exc:
        await make_staff(owner, business, user_id="64b7f8f8f8f8f8f8f8f8f8f8")
    assert exc.value.status_code == 422


async def test_staff_can_link_existing_user():
    owner = await make_owner()
    employee_user = await make_user(email="empleado@turnix.app")
    business = await make_business(owner)

    staff = await make_staff(owner, business, user_id=str(employee_user.id))
    assert staff.user_id == employee_user.id


async def test_update_staff_services_validated():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)
    staff = await make_staff(owner, business)

    updated = await staff_service.update_staff(
        owner, str(business.id), str(staff.id), StaffUpdate(services=[service.id])
    )
    assert updated.services == [service.id]


async def test_other_owner_cannot_manage_staff():
    owner = await make_owner()
    business = await make_business(owner)
    staff = await make_staff(owner, business)
    intruder = await make_owner(email="intruso@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await staff_service.get_staff(intruder, str(business.id), str(staff.id))
    assert exc.value.status_code == 403


async def test_staff_and_service_isolated_between_businesses():
    owner = await make_owner()
    business_a = await make_business(owner, name="A")
    business_b = await make_business(owner, name="B")
    staff_a = await make_staff(owner, business_a)

    with pytest.raises(HTTPException) as exc:
        await staff_service.get_staff(owner, str(business_b.id), str(staff_a.id))
    assert exc.value.status_code == 404


async def test_delete_staff():
    owner = await make_owner()
    business = await make_business(owner)
    staff = await make_staff(owner, business)

    await staff_service.delete_staff(owner, str(business.id), str(staff.id))

    assert await staff_service.list_staff(owner, str(business.id)) == []


async def test_create_staff_requires_owner():
    owner = await make_owner()
    business = await make_business(owner)
    customer = await make_user(email="cli@turnix.app", role="customer")

    with pytest.raises(HTTPException) as exc:
        await staff_service.create_staff(
            customer, str(business.id), StaffCreate(display_name="X")
        )
    assert exc.value.status_code == 403
