"""Tests del módulo de reportes avanzados del negocio."""

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import NamedTuple
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.db.repositories import waitlist_repository
from app.models import BookingStatus, Waitlist, WaitlistStatus
from app.schemas.blocked_period import BlockedPeriodCreate
from app.schemas.booking import BookingStatusUpdate
from app.services import blocked_period as blocked_period_service
from app.services import booking as booking_service
from app.services import reports as reports_service
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

PRICE_A = Decimal("10000")
PRICE_B = Decimal("20000")


class ReportSetup(NamedTuple):
    owner: object
    business: object
    service_a: object
    service_b: object
    staff_a: object
    staff_b: object
    customer: object
    day: object


async def _setup() -> ReportSetup:
    owner = await make_owner()
    business = await make_business(owner)
    service_a = await make_service(
        owner, business, name="Corte", duration_minutes=60, buffer_minutes=15, price=PRICE_A
    )
    service_b = await make_service(
        owner, business, name="Tinte", duration_minutes=30, buffer_minutes=0, price=PRICE_B
    )
    offered = [str(service_a.id), str(service_b.id)]
    staff_a = await make_staff(owner, business, display_name="Ana", services=offered)
    staff_b = await make_staff(owner, business, display_name="Beto", services=offered)
    customer = await make_user(email="cliente-reportes@turnix.app")
    day = next_open_day(0, days_ahead=8)
    return ReportSetup(
        owner, business, service_a, service_b, staff_a, staff_b, customer, day
    )


async def _complete(owner, business, booking) -> None:
    await booking_service.update_booking_status(
        owner,
        str(business.id),
        str(booking.id),
        BookingStatusUpdate(status=BookingStatus.COMPLETED),
    )


async def test_reports_empty_business():
    owner = await make_owner()
    business = await make_business(owner)

    report = await reports_service.get_business_reports(owner, str(business.id))

    assert report.revenue.total_revenue == Decimal(0)
    assert report.revenue.completed_bookings == 0
    assert report.revenue.average_ticket == Decimal(0)
    assert report.occupancy.available_minutes == 0
    assert report.occupancy.booked_minutes == 0
    assert report.profitability.revenue == Decimal(0)
    assert report.profitability.by_service == []
    assert report.waitlist.total_entries == 0
    assert report.customers.active_customers == 0
    assert report.customers.retention_rate is None


async def test_revenue_ticket_and_profitability():
    s = await _setup()
    previous_day = s.day - timedelta(days=7)
    previous = await make_booking(
        s.customer, s.business, s.service_a, s.staff_a, at(previous_day, 9, 0)
    )
    await _complete(s.owner, s.business, previous)

    for hour in (9, 10, 11):
        booking = await make_booking(
            s.customer, s.business, s.service_a, s.staff_a, at(s.day, hour, 0)
        )
        await _complete(s.owner, s.business, booking)
    await make_booking(s.customer, s.business, s.service_a, s.staff_a, at(s.day, 12, 0))
    completed_b = await make_booking(
        s.customer, s.business, s.service_b, s.staff_b, at(s.day, 9, 0)
    )
    await _complete(s.owner, s.business, completed_b)

    report = await reports_service.get_business_reports(
        s.owner, str(s.business.id), s.day, s.day + timedelta(days=6)
    )

    assert report.revenue.total_revenue == Decimal("50000")
    assert report.revenue.completed_bookings == 4
    assert report.revenue.average_ticket == Decimal("12500")
    assert report.revenue.previous_total_revenue == Decimal("10000")
    assert report.revenue.previous_average_ticket == Decimal("10000")
    assert report.revenue.revenue_change_percent == 400.0
    assert report.revenue.average_ticket_change_percent == 25.0
    assert len(report.revenue.daily) == 1
    assert report.revenue.daily[0].completed_bookings == 4
    assert [item.name for item in report.revenue.by_service] == ["Corte", "Tinte"]
    assert [item.name for item in report.revenue.by_staff] == ["Ana", "Beto"]

    assert report.profitability.revenue == Decimal("50000")
    assert report.profitability.slot_minutes == 255
    assert report.profitability.revenue_per_hour == Decimal("11764.71")
    profitability = {item.name: item for item in report.profitability.by_service}
    assert profitability["Corte"].slot_minutes == 225
    assert profitability["Corte"].revenue_per_hour == Decimal("8000.00")
    assert profitability["Tinte"].slot_minutes == 30
    assert profitability["Tinte"].revenue_per_hour == Decimal("40000.00")


async def test_occupancy_with_no_shows_and_blocked_periods():
    s = await _setup()
    for hour in (9, 10, 11):
        booking = await make_booking(
            s.customer, s.business, s.service_a, s.staff_a, at(s.day, hour, 0)
        )
        await _complete(s.owner, s.business, booking)
    await make_booking(s.customer, s.business, s.service_a, s.staff_a, at(s.day, 12, 0))
    no_show = await make_booking(
        s.customer, s.business, s.service_a, s.staff_a, at(s.day, 13, 0)
    )
    await booking_service.update_booking_status(
        s.owner,
        str(s.business.id),
        str(no_show.id),
        BookingStatusUpdate(status=BookingStatus.NO_SHOW),
    )
    completed_b = await make_booking(
        s.customer, s.business, s.service_b, s.staff_b, at(s.day, 9, 0)
    )
    await _complete(s.owner, s.business, completed_b)

    await blocked_period_service.create_block(
        s.owner,
        str(s.business.id),
        BlockedPeriodCreate(
            staff_id=s.staff_a.id,
            starts_at=at(s.day + timedelta(days=1), 9, 0),
            ends_at=at(s.day + timedelta(days=1), 10, 0),
            reason="Formación",
        ),
    )
    await blocked_period_service.create_block(
        s.owner,
        str(s.business.id),
        BlockedPeriodCreate(
            starts_at=at(s.day + timedelta(days=2), 9, 0),
            ends_at=at(s.day + timedelta(days=2), 10, 0),
            reason="Reunión",
        ),
    )

    report = await reports_service.get_business_reports(
        s.owner, str(s.business.id), s.day, s.day + timedelta(days=6)
    )

    assert report.occupancy.available_minutes == 5220
    assert report.occupancy.booked_minutes == 330
    assert report.occupancy.idle_minutes == 4890
    assert report.occupancy.no_show_minutes == 60
    assert report.occupancy.occupancy_rate == 6.3
    staff = {item.name: item for item in report.occupancy.by_staff}
    assert staff["Ana"].available_minutes == 2580
    assert staff["Ana"].booked_minutes == 300
    assert staff["Ana"].no_show_minutes == 60
    assert staff["Ana"].occupancy_rate == 11.6
    assert staff["Beto"].available_minutes == 2640
    assert staff["Beto"].booked_minutes == 30
    assert staff["Beto"].occupancy_rate == 1.1


async def test_waitlist_report_counts_and_estimated_value():
    owner = await make_owner()
    business = await make_business(owner)
    service_a = await make_service(owner, business, name="Corte", price=PRICE_A)
    service_b = await make_service(owner, business, name="Tinte", price=PRICE_B)
    staff_a = await make_staff(owner, business, display_name="Ana")
    staff_b = await make_staff(owner, business, display_name="Beto")
    tz = ZoneInfo(business.timezone)
    today = datetime.now(tz).date()
    created_at = datetime.combine(today, time(12, 0), tzinfo=tz).astimezone(UTC)

    entries = [
        Waitlist(
            business_id=business.id,
            service_id=service_a.id,
            staff_id=staff_a.id,
            customer_name="Uno",
            status=WaitlistStatus.BOOKED,
            created_at=created_at,
            updated_at=created_at,
        ),
        Waitlist(
            business_id=business.id,
            service_id=service_a.id,
            staff_id=staff_a.id,
            customer_name="Dos",
            status=WaitlistStatus.EXPIRED,
            created_at=created_at,
            updated_at=created_at,
        ),
        Waitlist(
            business_id=business.id,
            service_id=service_b.id,
            staff_id=staff_b.id,
            customer_name="Tres",
            status=WaitlistStatus.WAITING,
            created_at=created_at,
            updated_at=created_at,
        ),
        Waitlist(
            business_id=business.id,
            service_id=service_b.id,
            staff_id=staff_b.id,
            customer_name="Cuatro",
            status=WaitlistStatus.OFFERED,
            created_at=created_at,
            updated_at=created_at,
        ),
        Waitlist(
            business_id=business.id,
            customer_name="Cinco",
            status=WaitlistStatus.CANCELLED,
            created_at=created_at,
            updated_at=created_at,
        ),
    ]
    for entry in entries:
        await waitlist_repository.insert(entry)

    report = await reports_service.get_business_reports(
        owner, str(business.id), today, today
    )

    waitlist = report.waitlist
    assert waitlist.total_entries == 5
    assert waitlist.by_status == {
        "waiting": 1,
        "offered": 1,
        "booked": 1,
        "expired": 1,
        "cancelled": 1,
    }
    assert waitlist.conversion_rate == 20.0
    assert waitlist.lost_rate == 40.0
    assert waitlist.estimated_value == Decimal("60000")
    assert waitlist.estimated_converted_value == Decimal("10000")
    by_service = {item.name: item for item in waitlist.by_service}
    assert by_service["Corte"].total == 2
    assert by_service["Corte"].conversion_rate == 50.0
    assert by_service["Corte"].estimated_value == Decimal("20000")
    assert by_service["Tinte"].total == 2
    assert by_service["Tinte"].conversion_rate == 0.0
    assert by_service["Sin servicio"].total == 1


async def test_customer_new_returning_repeat_and_retention():
    owner = await make_owner()
    business = await make_business(owner)
    service = await make_service(owner, business, name="Corte", price=PRICE_A)
    staff = await make_staff(owner, business, display_name="Ana", services=[str(service.id)])
    customer_a = await make_user(
        email="ana-reportes@turnix.app", full_name="Ana Cliente"
    )
    customer_b = await make_user(
        email="beto-reportes@turnix.app", full_name="Beto Cliente"
    )
    customer_c = await make_user(
        email="carla-reportes@turnix.app", full_name="Carla Cliente"
    )
    period_day = next_open_day(0, days_ahead=15)
    prior_day = period_day - timedelta(days=7)

    prior_a = await make_booking(
        customer_a, business, service, staff, at(prior_day, 9, 0)
    )
    await _complete(owner, business, prior_a)
    period_a_1 = await make_booking(
        customer_a, business, service, staff, at(period_day, 9, 0)
    )
    period_a_2 = await make_booking(
        customer_a, business, service, staff, at(period_day + timedelta(days=1), 9, 0)
    )
    await _complete(owner, business, period_a_1)
    await _complete(owner, business, period_a_2)
    period_b = await make_booking(
        customer_b, business, service, staff, at(period_day, 11, 0)
    )
    await _complete(owner, business, period_b)
    prior_c = await make_booking(
        customer_c, business, service, staff, at(prior_day, 10, 0)
    )
    await _complete(owner, business, prior_c)

    report = await reports_service.get_business_reports(
        owner,
        str(business.id),
        period_day,
        period_day + timedelta(days=1),
    )

    customers = report.customers
    assert customers.active_customers == 2
    assert customers.new_customers == 1
    assert customers.returning_customers == 1
    assert customers.repeat_customers == 1
    assert customers.inactive_customers_count == 1
    assert customers.new_customer_rate == 50.0
    assert customers.repeat_rate == 50.0
    assert customers.retention_rate == 50.0
    assert customers.average_visits_per_customer == 1.5
    assert customers.average_days_between_visits == 4.0
    assert [item.name for item in customers.top_customers] == [
        "Ana Cliente",
        "Beto Cliente",
    ]
    assert customers.top_customers[0].visits == 2
    assert customers.top_customers[0].completed_revenue == Decimal("20000")
    assert [item.name for item in customers.inactive_customers] == ["Carla Cliente"]


async def test_reports_invalid_range_and_forbidden():
    s = await _setup()
    intruder = await make_user(email="intruso-reportes@turnix.app")

    with pytest.raises(HTTPException) as exc:
        await reports_service.get_business_reports(
            s.owner, str(s.business.id), s.day, s.day - timedelta(days=5)
        )
    assert exc.value.status_code == 422

    with pytest.raises(HTTPException) as exc:
        await reports_service.get_business_reports(intruder, str(s.business.id))
    assert exc.value.status_code == 403


async def test_reports_endpoint_over_http(client):
    owner = await make_owner()
    business = await make_business(owner)
    day = next_open_day(0, days_ahead=8)

    assert (
        await client.get(f"/api/v1/businesses/{business.id}/reports")
    ).status_code == 401

    login = await client.post(
        "/api/v1/auth/login", json={"email": "owner@turnix.app", "password": "secreto123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get(
        f"/api/v1/businesses/{business.id}/reports",
        params={"date_from": day.isoformat(), "date_to": day.isoformat()},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["timezone"] == business.timezone
    assert Decimal(body["revenue"]["total_revenue"]) == Decimal(0)
    assert body["customers"]["active_customers"] == 0

    invalid = await client.get(
        f"/api/v1/businesses/{business.id}/reports",
        params={
            "date_from": day.isoformat(),
            "date_to": (day - timedelta(days=5)).isoformat(),
        },
        headers=headers,
    )
    assert invalid.status_code == 422
