"""Tests del motor de reservas: disponibilidad, validaciones y permisos."""

from datetime import timedelta
from typing import NamedTuple

import pytest
from fastapi import HTTPException

from app.models import BookingStatus
from app.schemas.booking import BookingStatusUpdate
from app.services import booking as booking_service
from tests.factories import (
    at,
    make_booking,
    make_business,
    make_owner,
    make_service,
    make_staff,
    make_user,
    next_open_day,
)


class Setup(NamedTuple):
    """Entidades creadas por `_setup` para un negocio listo para reservar."""

    owner: object
    business: object
    service: object
    staff: object


async def _setup(duration=60, buffer=0, **staff_kwargs) -> Setup:
    """Crea negocio + servicio + empleado listos para reservar."""
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(
        owner, business, duration_minutes=duration, buffer_minutes=buffer
    )
    staff = await make_staff(owner, business, services=[str(service.id)], **staff_kwargs)
    return Setup(owner, business, service, staff)


async def test_availability_returns_slots_within_business_hours():
    s = await _setup()
    day = next_open_day(0)  # lunes

    result = await booking_service.get_availability(
        str(s.business.id), str(s.service.id), str(s.staff.id), day
    )

    assert result.timezone == s.business.timezone
    starts = [slot.start_at.strftime("%H:%M") for slot in result.slots]
    assert starts[0] == "09:00"
    assert starts[-1] == "17:00"
    assert len(result.slots) == 33


async def test_availability_requires_staff_to_offer_service():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business)
    staff = await make_staff(owner, business, services=[])  # sin servicios
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await booking_service.get_availability(
            str(business.id), str(service.id), str(staff.id), day
        )
    assert exc.value.status_code == 422


async def test_create_booking_sets_price_and_customer():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, s.business, s.service, s.staff, at(day, 14, 30))

    assert reservation.status == BookingStatus.PENDING
    assert reservation.customer_id == customer.id
    assert str(reservation.price) == str(s.service.price)
    assert reservation.currency == s.business.currency
    assert reservation.end_at - reservation.start_at == timedelta(
        minutes=s.service.duration_minutes
    )


async def test_booking_removes_slot_from_availability():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    await make_booking(customer, s.business, s.service, s.staff, at(day, 14, 30))

    result = await booking_service.get_availability(
        str(s.business.id), str(s.service.id), str(s.staff.id), day
    )
    occupied = {slot.start_at.strftime("%H:%M") for slot in result.slots}
    assert "14:30" not in occupied  # el propio hueco reservado
    assert "14:00" not in occupied  # 14:00-15:00 solapa 14:30-15:30
    assert "13:45" not in occupied  # 13:45-14:45 solapa 14:30-15:30
    assert "13:30" in occupied      # 13:30-14:30 termina justo a las 14:30 (no solapa)
    assert "13:00" in occupied      # 13:00-14:00 termina antes


async def test_booking_on_occupied_slot_is_conflict():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))

    with pytest.raises(HTTPException) as exc:
        await make_booking(customer, s.business, s.service, s.staff, at(day, 10, 0))
    assert exc.value.status_code == 409


async def test_booking_outside_hours_is_conflict():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await make_booking(customer, s.business, s.service, s.staff, at(day, 7, 0))
    assert exc.value.status_code == 409


async def test_booking_on_closed_day_is_conflict():
    """El domingo el negocio está cerrado por defecto."""
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    sunday = next_open_day(6)

    with pytest.raises(HTTPException) as exc:
        await make_booking(customer, s.business, s.service, s.staff, at(sunday, 12, 0))
    assert exc.value.status_code == 409


async def test_confirmed_booking_also_blocks_slot():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, s.business, s.service, s.staff, at(day, 11, 0))
    await booking_service.update_booking_status(
        s.owner,
        str(s.business.id),
        str(reservation.id),
        BookingStatusUpdate(status=BookingStatus.CONFIRMED),
    )

    with pytest.raises(HTTPException) as exc:
        await make_booking(customer, s.business, s.service, s.staff, at(day, 11, 0))
    assert exc.value.status_code == 409


async def test_cancelled_booking_frees_slot_again():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, s.business, s.service, s.staff, at(day, 11, 0))
    await booking_service.update_booking_status(
        s.owner,
        str(s.business.id),
        str(reservation.id),
        BookingStatusUpdate(status=BookingStatus.CANCELLED),
    )

    result = await booking_service.get_availability(
        str(s.business.id), str(s.service.id), str(s.staff.id), day
    )
    assert "11:00" in {slot.start_at.strftime("%H:%M") for slot in result.slots}


async def test_client_lists_only_own_bookings():
    s = await _setup()
    alice = await make_user(email="alice@turnix.app")
    bob = await make_user(email="bob@turnix.app")
    day = next_open_day(0)
    await make_booking(alice, s.business, s.service, s.staff, at(day, 9, 0))
    await make_booking(bob, s.business, s.service, s.staff, at(day, 10, 0))

    assert len(await booking_service.list_my_bookings(alice)) == 1
    assert len(await booking_service.list_my_bookings(bob)) == 1


async def test_client_cannot_list_business_bookings():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    await make_booking(customer, s.business, s.service, s.staff, at(day, 9, 0))

    with pytest.raises(HTTPException) as exc:
        await booking_service.list_business_bookings(customer, str(s.business.id))
    assert exc.value.status_code == 403


async def test_client_cannot_confirm_own_booking():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, s.business, s.service, s.staff, at(day, 9, 0))

    with pytest.raises(HTTPException) as exc:
        await booking_service.update_booking_status(
            customer,
            str(s.business.id),
            str(reservation.id),
            BookingStatusUpdate(status=BookingStatus.CONFIRMED),
        )
    assert exc.value.status_code == 403


async def test_client_can_cancel_own_booking():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, s.business, s.service, s.staff, at(day, 9, 0))

    updated = await booking_service.update_booking_status(
        customer,
        str(s.business.id),
        str(reservation.id),
        BookingStatusUpdate(status=BookingStatus.CANCELLED, cancellation_reason="No puedo"),
    )
    assert updated.status == BookingStatus.CANCELLED
    assert updated.cancellation_reason == "No puedo"


async def test_other_customer_cannot_read_booking():
    s = await _setup()
    alice = await make_user(email="alice@turnix.app")
    bob = await make_user(email="bob@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(alice, s.business, s.service, s.staff, at(day, 9, 0))

    with pytest.raises(HTTPException) as exc:
        await booking_service.get_booking(bob, str(s.business.id), str(reservation.id))
    assert exc.value.status_code == 403


async def test_owner_deletes_booking():
    s = await _setup()
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    reservation = await make_booking(customer, s.business, s.service, s.staff, at(day, 9, 0))

    await booking_service.delete_booking(s.owner, str(s.business.id), str(reservation.id))

    result = await booking_service.get_availability(
        str(s.business.id), str(s.service.id), str(s.staff.id), day
    )
    assert "09:00" in {slot.start_at.strftime("%H:%M") for slot in result.slots}
