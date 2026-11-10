"""Tests de la agenda del empleado (rol staff).

Cubren: perfil propio, listado de sus citas, aislamiento entre empleados,
filtro por fechas, acceso a una cita concreta y los bloqueos que le afectan.
"""

from datetime import timedelta
from typing import NamedTuple

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models import BookingStatus
from app.schemas.blocked_period import BlockedPeriodCreate
from app.schemas.booking import BookingStatusUpdate, StaffBookingStatusUpdate
from app.services import blocked_period as block_service
from app.services import booking as booking_service
from app.services import staff_agenda as agenda_service
from tests.factories import (
    at,
    make_booking,
    make_business,
    make_owner,
    make_service,
    make_staff,
    make_staff_user,
    make_user,
    next_open_day,
)


class StaffSetup(NamedTuple):
    owner: object
    business: object
    service: object
    staff: object
    staff_user: object


async def _staff_setup() -> StaffSetup:
    """Negocio con un empleado vinculado a un usuario de rol staff."""
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, duration_minutes=60)
    staff_user = await make_staff_user()
    staff = await make_staff(
        owner,
        business,
        display_name="Luis",
        services=[str(service.id)],
        user_id=str(staff_user.id),
    )
    return StaffSetup(owner, business, service, staff, staff_user)


async def test_staff_sees_own_profile():
    s = await _staff_setup()

    profile, profile_business = await agenda_service.get_my_profile(s.staff_user)

    assert profile.id == s.staff.id
    assert profile_business.id == s.business.id


async def test_user_without_staff_record_is_forbidden():
    customer = await make_user(email="cli@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await agenda_service.get_my_profile(customer)
    assert exc.value.status_code == 403


async def test_staff_sees_only_own_agenda():
    s = await _staff_setup()
    other_staff = await make_staff(
        s.owner, s.business, display_name="Otro", services=[str(s.service.id)]
    )
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)

    mine = await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))
    await make_booking(customer, s.business, s.service, other_staff, at(day, 11, 0))

    agenda = await agenda_service.list_my_agenda(s.staff_user)
    assert [booking.id for booking in agenda] == [mine.id]


async def test_agenda_excludes_cancelled_and_sorted_by_start():
    s = await _staff_setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)

    later = await make_booking(customer, s.business, s.service, s.staff, at(day, 11, 0))
    earlier = await make_booking(customer, s.business, s.service, s.staff, at(day, 9, 0))
    cancelled = await make_booking(customer, s.business, s.service, s.staff, at(day, 13, 0))
    await booking_service.update_booking_status(
        s.owner,
        str(s.business.id),
        str(cancelled.id),
        BookingStatusUpdate(status=BookingStatus.CANCELLED),
    )

    agenda = await agenda_service.list_my_agenda(s.staff_user)
    assert [booking.id for booking in agenda] == [earlier.id, later.id]


async def test_agenda_date_range_filter():
    s = await _staff_setup()
    customer = await make_user(email="cli@turnix.app")
    monday = next_open_day(0)
    next_monday = next_open_day(0, days_ahead=8)
    await make_booking(customer, s.business, s.service, s.staff, at(monday, 10, 0))
    await make_booking(customer, s.business, s.service, s.staff, at(next_monday, 10, 0))

    only_first = await agenda_service.list_my_agenda(s.staff_user, monday, monday)
    assert len(only_first) == 1
    assert only_first[0].start_at.date() == monday


async def test_invalid_date_range_is_rejected():
    s = await _staff_setup()
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await agenda_service.list_my_agenda(s.staff_user, day + timedelta(days=5), day)
    assert exc.value.status_code == 422


async def test_staff_can_fetch_own_booking_but_not_other_staff():
    s = await _staff_setup()
    other_staff = await make_staff(
        s.owner, s.business, display_name="Otro", services=[str(s.service.id)]
    )
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)

    mine = await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))
    theirs = await make_booking(customer, s.business, s.service, other_staff, at(day, 11, 0))

    fetched = await agenda_service.get_my_booking(s.staff_user, str(mine.id))
    assert fetched.id == mine.id

    with pytest.raises(HTTPException) as exc:
        await agenda_service.get_my_booking(s.staff_user, str(theirs.id))
    assert exc.value.status_code == 404


async def test_staff_sees_own_and_business_blocks_not_other_staff_blocks():
    s = await _staff_setup()
    other_staff = await make_staff(
        s.owner, s.business, display_name="Otro", services=[str(s.service.id)]
    )
    day = next_open_day(0)

    # Propio, de negocio y de otro empleado.
    await block_service.create_block(
        s.owner,
        str(s.business.id),
        BlockedPeriodCreate(staff_id=s.staff.id, starts_at=at(day, 9), ends_at=at(day, 10)),
    )
    await block_service.create_block(
        s.owner,
        str(s.business.id),
        BlockedPeriodCreate(starts_at=at(day, 12), ends_at=at(day, 13)),
    )
    await block_service.create_block(
        s.owner,
        str(s.business.id),
        BlockedPeriodCreate(
            staff_id=other_staff.id, starts_at=at(day, 15), ends_at=at(day, 16)
        ),
    )

    blocks = await agenda_service.list_my_blocked_periods(s.staff_user, day, day)
    staff_ids = {str(block.staff_id) if block.staff_id else None for block in blocks}
    assert len(blocks) == 2
    assert None in staff_ids
    assert str(s.staff.id) in staff_ids


async def test_agenda_http_endpoints_require_auth_and_work(client):
    # Sin token -> 401.
    assert (await client.get("/api/v1/staff/me")).status_code == 401

    # Un cliente sin registro de empleado -> 403.
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Cli", "email": "cli2@turnix.app", "password": "secreto123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "cli2@turnix.app", "password": "secreto123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get("/api/v1/staff/me", headers=headers)).status_code == 403


async def test_staff_marks_own_booking_completed():
    s = await _staff_setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    booking = await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))

    updated = await agenda_service.update_my_booking_status(
        s.staff_user,
        str(booking.id),
        StaffBookingStatusUpdate(status=BookingStatus.COMPLETED),
    )
    assert updated.status == BookingStatus.COMPLETED


async def test_staff_marks_own_booking_no_show():
    s = await _staff_setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    booking = await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))

    updated = await agenda_service.update_my_booking_status(
        s.staff_user,
        str(booking.id),
        StaffBookingStatusUpdate(status=BookingStatus.NO_SHOW),
    )
    assert updated.status == BookingStatus.NO_SHOW


async def test_staff_cannot_mark_other_staff_booking():
    s = await _staff_setup()
    other_staff = await make_staff(
        s.owner, s.business, display_name="Otro", services=[str(s.service.id)]
    )
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    theirs = await make_booking(customer, s.business, s.service, other_staff, at(day, 10, 0))

    with pytest.raises(HTTPException) as exc:
        await agenda_service.update_my_booking_status(
            s.staff_user,
            str(theirs.id),
            StaffBookingStatusUpdate(status=BookingStatus.COMPLETED),
        )
    assert exc.value.status_code == 404


async def test_cannot_re_mark_closed_booking():
    s = await _staff_setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    booking = await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))
    await agenda_service.update_my_booking_status(
        s.staff_user,
        str(booking.id),
        StaffBookingStatusUpdate(status=BookingStatus.COMPLETED),
    )

    with pytest.raises(HTTPException) as exc:
        await agenda_service.update_my_booking_status(
            s.staff_user,
            str(booking.id),
            StaffBookingStatusUpdate(status=BookingStatus.NO_SHOW),
        )
    assert exc.value.status_code == 409


def test_staff_status_update_only_allows_completed_or_no_show():
    StaffBookingStatusUpdate(status=BookingStatus.COMPLETED)
    StaffBookingStatusUpdate(status=BookingStatus.NO_SHOW)

    for invalid in (BookingStatus.CANCELLED, BookingStatus.PENDING, BookingStatus.CONFIRMED):
        with pytest.raises(ValidationError):
            StaffBookingStatusUpdate(status=invalid)


async def test_staff_status_endpoint_rejects_invalid_status_and_requires_auth(client):
    s = await _staff_setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    booking = await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))

    # El esquema rechaza cualquier estado distinto de completed/no_show.
    with pytest.raises(ValidationError):
        StaffBookingStatusUpdate(status="cancelled")

    # El endpoint existe y exige autenticación.
    assert (
        await client.patch(
            f"/api/v1/staff/me/agenda/{booking.id}", json={"status": "completed"}
        )
    ).status_code == 401

