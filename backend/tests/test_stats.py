"""Tests del dashboard de estadísticas del negocio."""

from datetime import timedelta
from decimal import Decimal
from typing import NamedTuple

import pytest
from fastapi import HTTPException

from app.models import BookingStatus
from app.schemas.booking import BookingStatusUpdate
from app.services import booking as booking_service
from app.services import stats as stats_service
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
    owner: object
    business: object
    service_a: object
    service_b: object
    staff1: object
    staff2: object
    customer: object


async def _setup() -> Setup:
    """Negocio con dos servicios, dos empleados y reservas variadas."""
    owner = await make_owner()
    business = await make_business(owner)
    service_a = await make_service(owner, business, name="Corte", price=Decimal("10000"))
    service_b = await make_service(owner, business, name="Tinte", price=Decimal("20000"))
    offered = [str(service_a.id), str(service_b.id)]
    staff1 = await make_staff(owner, business, display_name="Ana", services=offered)
    staff2 = await make_staff(owner, business, display_name="Beto", services=offered)
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)

    async def book(service, staff, hour):
        return await make_booking(customer, business, service, staff, at(day, hour, 0))

    async def complete(booking):
        await booking_service.update_booking_status(
            owner,
            str(business.id),
            str(booking.id),
            BookingStatusUpdate(status=BookingStatus.COMPLETED),
        )

    # 3 completadas del servicio A con Ana, más 1 pendiente.
    await complete(await book(service_a, staff1, 9))
    await complete(await book(service_a, staff1, 10))
    await complete(await book(service_a, staff1, 11))
    await book(service_a, staff1, 12)

    # 1 completada y 1 cancelada del servicio B con Beto.
    await complete(await book(service_b, staff2, 9))
    cancelled = await book(service_b, staff2, 10)
    await booking_service.update_booking_status(
        owner,
        str(business.id),
        str(cancelled.id),
        BookingStatusUpdate(status=BookingStatus.CANCELLED),
    )

    return Setup(owner, business, service_a, service_b, staff1, staff2, customer)


async def test_stats_empty_business():
    owner = await make_owner()
    business = await make_business(owner)

    stats = await stats_service.get_business_stats(owner, str(business.id))

    assert stats.total_bookings == 0
    assert stats.revenue_completed == Decimal(0)
    assert stats.bookings_by_status[BookingStatus.COMPLETED.value] == 0
    assert stats.bookings_by_status[BookingStatus.PENDING.value] == 0
    assert stats.top_services == []
    assert stats.top_staff == []


async def test_stats_counts_and_revenue():
    s = await _setup()

    stats = await stats_service.get_business_stats(s.owner, str(s.business.id))

    assert stats.total_bookings == 6
    assert stats.bookings_by_status[BookingStatus.COMPLETED.value] == 4
    assert stats.bookings_by_status[BookingStatus.PENDING.value] == 1
    assert stats.bookings_by_status[BookingStatus.CANCELLED.value] == 1
    assert stats.bookings_by_status[BookingStatus.CONFIRMED.value] == 0
    # 3 * 10000 (A completadas) + 1 * 20000 (B completada).
    assert stats.revenue_completed == Decimal("50000")
    assert stats.currency == s.business.currency


async def test_stats_top_services_and_staff_exclude_cancelled():
    s = await _setup()

    stats = await stats_service.get_business_stats(s.owner, str(s.business.id))

    assert [item.name for item in stats.top_services] == ["Corte", "Tinte"]
    assert stats.top_services[0].count == 4
    assert stats.top_services[1].count == 1

    assert [item.name for item in stats.top_staff] == ["Ana", "Beto"]
    assert stats.top_staff[0].count == 4
    assert stats.top_staff[1].count == 1


async def test_stats_date_range_filter():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, name="Corte", price=Decimal("10000"))
    staff = await make_staff(owner, business, display_name="Ana", services=[str(service.id)])
    customer = await make_user(email="cli@turnix.app")
    day = next_open_day(0)
    later = next_open_day(0, days_ahead=8)

    await make_booking(customer, business, service, staff, at(day, 9, 0))
    await make_booking(customer, business, service, staff, at(later, 9, 0))

    only_first = await stats_service.get_business_stats(
        owner, str(business.id), day, day
    )
    assert only_first.total_bookings == 1


async def test_stats_invalid_range_is_422():
    s = await _setup()
    day = next_open_day(0)

    with pytest.raises(HTTPException) as exc:
        await stats_service.get_business_stats(
            s.owner, str(s.business.id), day, day - timedelta(days=5)
        )
    assert exc.value.status_code == 422


async def test_stats_forbidden_for_non_manager():
    s = await _setup()
    intruder = await make_user(email="intruso@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await stats_service.get_business_stats(intruder, str(s.business.id))
    assert exc.value.status_code == 403


async def test_stats_endpoint_over_http(client):
    s = await _setup()

    # Sin token -> 401.
    assert (
        await client.get(f"/api/v1/businesses/{s.business.id}/stats")
    ).status_code == 401

    login = await client.post(
        "/api/v1/auth/login", json={"email": "owner@turnix.app", "password": "secreto123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get(
        f"/api/v1/businesses/{s.business.id}/stats", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_bookings"] == 6
    assert body["bookings_by_status"]["completed"] == 4
