"""Tests del CRUD de bloqueos de agenda."""

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.schemas.blocked_period import BlockedPeriodCreate, BlockedPeriodUpdate
from app.services import blocked_period as block_service
from app.services import booking as booking_service
from tests.factories import (
    at,
    make_business,
    make_owner,
    make_service,
    make_staff,
    next_open_day,
)


async def test_create_business_wide_block():
    owner = await make_owner()
    business = await make_business(owner)
    day = next_open_day(0)

    block = await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(starts_at=at(day, 12), ends_at=at(day, 14), reason="Reunión"),
    )

    assert block.staff_id is None
    assert block.reason == "Reunión"
    assert block.business_id == business.id


async def test_create_staff_specific_block():
    owner = await make_owner()
    business = await make_business(owner)
    staff = await make_staff(owner, business)
    day = next_open_day(0)

    block = await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(
            staff_id=staff.id, starts_at=at(day, 9), ends_at=at(day, 10), reason="Personal"
        ),
    )

    assert block.staff_id == staff.id


async def test_block_with_invalid_range_is_rejected():
    owner = await make_owner()
    business = await make_business(owner)
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await block_service.create_block(
            owner,
            str(business.id),
            BlockedPeriodCreate(starts_at=at(day, 14), ends_at=at(day, 14)),
        )
    assert exc.value.status_code == 422


async def test_block_with_staff_from_other_business_is_rejected():
    owner = await make_owner()
    business_a = await make_business(owner, name="A")
    business_b = await make_business(owner, name="B")
    foreign_staff = await make_staff(owner, business_b)
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await block_service.create_block(
            owner,
            str(business_a.id),
            BlockedPeriodCreate(
                staff_id=foreign_staff.id, starts_at=at(day, 9), ends_at=at(day, 10)
            ),
        )
    assert exc.value.status_code == 422


async def test_update_block_range_is_validated_against_existing():
    owner = await make_owner()
    business = await make_business(owner)
    day = next_open_day(0)
    block = await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(starts_at=at(day, 9), ends_at=at(day, 10)),
    )

    updated = await block_service.update_block(
        owner, str(business.id), str(block.id), BlockedPeriodUpdate(reason="Nuevo motivo")
    )
    assert updated.reason == "Nuevo motivo"

    with pytest.raises(HTTPException) as exc:
        await block_service.update_block(
            owner, str(business.id), str(block.id), BlockedPeriodUpdate(ends_at=at(day, 9))
        )
    assert exc.value.status_code == 422


async def test_other_owner_cannot_manage_blocks():
    owner = await make_owner()
    business = await make_business(owner)
    intruder = await make_owner(email="intruso@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await block_service.list_blocks(intruder, str(business.id))
    assert exc.value.status_code == 403


async def test_get_block_with_invalid_id_is_404():
    owner = await make_owner()
    business = await make_business(owner)

    with pytest.raises(HTTPException) as exc:
        await block_service.get_block(owner, str(business.id), "no-es-un-id")
    assert exc.value.status_code == 404


async def test_delete_block():
    owner = await make_owner()
    business = await make_business(owner)
    day = next_open_day(0)
    block = await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(starts_at=at(day, 9), ends_at=at(day, 10)),
    )

    await block_service.delete_block(owner, str(business.id), str(block.id))

    assert await block_service.list_blocks(owner, str(business.id)) == []


async def test_business_block_removes_availability():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, duration_minutes=60)
    staff = await make_staff(owner, business, services=[str(service.id)])
    day = next_open_day(0)

    before = await booking_service.get_availability(
        str(business.id), str(service.id), str(staff.id), day
    )
    await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(starts_at=at(day, 12), ends_at=at(day, 14)),
    )
    after = await booking_service.get_availability(
        str(business.id), str(service.id), str(staff.id), day
    )

    # Un bloqueo de 2 h con servicio de 60 min quita 11 huecos (11:15..13:45).
    assert len(before.slots) - len(after.slots) == 11
    blocked = {slot.start_at.strftime("%H:%M") for slot in after.slots}
    assert "12:00" not in blocked
    assert "13:00" not in blocked


async def test_staff_block_only_affects_that_staff():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, duration_minutes=60)
    staff_a = await make_staff(owner, business, services=[str(service.id)], display_name="A")
    staff_b = await make_staff(owner, business, services=[str(service.id)], display_name="B")
    day = next_open_day(0)

    await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(
            staff_id=staff_a.id, starts_at=at(day, 12), ends_at=at(day, 14)
        ),
    )

    avail_a = await booking_service.get_availability(
        str(business.id), str(service.id), str(staff_a.id), day
    )
    avail_b = await booking_service.get_availability(
        str(business.id), str(service.id), str(staff_b.id), day
    )

    assert "12:00" not in {slot.start_at.strftime("%H:%M") for slot in avail_a.slots}
    assert "12:00" in {slot.start_at.strftime("%H:%M") for slot in avail_b.slots}


async def test_block_duration_math_is_consistent():
    """Comprobación ligera de coherencia temporal del bloqueo."""
    owner = await make_owner()
    business = await make_business(owner)
    day = next_open_day(0)
    block = await block_service.create_block(
        owner,
        str(business.id),
        BlockedPeriodCreate(starts_at=at(day, 9), ends_at=at(day, 10, 30)),
    )
    assert block.ends_at - block.starts_at == timedelta(hours=1, minutes=30)
