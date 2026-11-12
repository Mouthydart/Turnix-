"""Lógica de negocio del módulo de reportes del negocio.

Incluye:
1. Ingresos y ticket promedio.
2. Ocupación real de la agenda.
3. Rentabilidad por hora de agenda.
6. Lista de espera y demanda no atendida.
9. Clientes nuevos, recurrentes y retención.

Todos los cálculos se hacen sobre las reservas y entidades existentes; no se
modifica el modelo de datos. Los rangos de fechas se interpretan en la zona
horaria del negocio.
"""

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from itertools import pairwise
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app.db.repositories import (
    blocked_period_repository,
    booking_repository,
    service_repository,
    staff_repository,
    user_repository,
    waitlist_repository,
)
from app.models import (
    Booking,
    BookingStatus,
    Business,
    Service,
    Staff,
    User,
    Waitlist,
    WaitlistStatus,
)
from app.schemas.reports import (
    BusinessReports,
    CustomerReport,
    CustomerSummary,
    OccupancyDay,
    OccupancyReport,
    OccupancyStaff,
    ProfitabilityReport,
    RevenueBreakdown,
    RevenueDay,
    RevenueReport,
    ServiceProfitability,
    WaitlistBreakdown,
    WaitlistReport,
)
from app.services.availability import schedule_for_date
from app.services.business import get_managed_business

CANCELLED_STATUSES = {BookingStatus.CANCELLED}
CUSTOMER_STATUSES = {
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
    BookingStatus.COMPLETED,
    BookingStatus.NO_SHOW,
}
MONEY_PRECISION = Decimal("0.01")


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail
    )


def _resolve_range(
    date_from: date | None, date_to: date | None, tz: ZoneInfo
) -> tuple[date, date, datetime, datetime]:
    """Normaliza el rango y lo convierte a límites UTC semiabiertos."""
    today = datetime.now(tz).date()

    if date_from is None and date_to is None:
        date_from = today.replace(day=1)
        date_to = today
    elif date_from is None:
        date_from = date_to.replace(day=1)  # type: ignore[union-attr]
    elif date_to is None:
        date_to = today

    if date_to < date_from:  # type: ignore[operator]
        raise _unprocessable("`date_to` no puede ser anterior a `date_from`")

    start = datetime.combine(date_from, time(0, 0), tzinfo=tz).astimezone(UTC)
    end = datetime.combine(
        date_to + timedelta(days=1), time(0, 0), tzinfo=tz
    ).astimezone(UTC)
    return date_from, date_to, start, end


def _previous_range(date_from: date, date_to: date) -> tuple[date, date]:
    """Devuelve el periodo inmediatamente anterior de la misma duración."""
    days = (date_to - date_from).days + 1
    previous_to = date_from - timedelta(days=1)
    previous_from = previous_to - timedelta(days=days - 1)
    return previous_from, previous_to


def _range_bounds(date_from: date, date_to: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(date_from, time(0, 0), tzinfo=tz).astimezone(UTC)
    end = datetime.combine(
        date_to + timedelta(days=1), time(0, 0), tzinfo=tz
    ).astimezone(UTC)
    return start, end


def _iter_dates(date_from: date, date_to: date):
    current = date_from
    while current <= date_to:
        yield current
        current += timedelta(days=1)


def _minutes_between(start: datetime, end: datetime) -> float:
    return max((end - start).total_seconds() / 60, 0)


def _sum_minutes(intervals: list[tuple[datetime, datetime]]) -> int:
    return round(sum(_minutes_between(start, end) for start, end in intervals))


def _intersection_minutes(
    start: datetime, end: datetime, intervals: list[tuple[datetime, datetime]]
) -> float:
    """Minutos del rango que caen dentro de algunos de los intervalos."""
    total = 0.0
    for interval_start, interval_end in intervals:
        overlap_start = max(start, interval_start)
        overlap_end = min(end, interval_end)
        if overlap_end > overlap_start:
            total += _minutes_between(overlap_start, overlap_end)
    return total


def _subtract_intervals(
    base: list[tuple[datetime, datetime]],
    cuts: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Resta los intervalos `cuts` de los intervalos `base`."""
    result: list[tuple[datetime, datetime]] = []
    for start, end in base:
        segments = [(start, end)]
        for cut_start, cut_end in cuts:
            remaining: list[tuple[datetime, datetime]] = []
            for segment_start, segment_end in segments:
                if cut_end <= segment_start or cut_start >= segment_end:
                    remaining.append((segment_start, segment_end))
                    continue
                if segment_start < cut_start:
                    remaining.append((segment_start, cut_start))
                if cut_end < segment_end:
                    remaining.append((cut_end, segment_end))
            segments = remaining
        result.extend(segments)
    return result


def _schedule_intervals(
    business: Business, staff: Staff | None, target_date: date, tz: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    """Franjas de horario del negocio/empleado para un día local."""
    day = schedule_for_date(business, staff, target_date)
    if day is None or day.is_closed:
        return []
    return [
        (
            datetime.combine(target_date, interval.open, tzinfo=tz),
            datetime.combine(target_date, interval.close, tzinfo=tz),
        )
        for interval in day.intervals
    ]


def _percentage(value: int | float, total: int | float) -> float:
    if total == 0:
        return 0.0
    return round(float(value) / float(total) * 100, 1)


def _change_percent(current: Decimal, previous: Decimal) -> float | None:
    if previous == 0:
        return None
    return round(float((current - previous) / previous * 100), 1)


def _average(total: Decimal, count: int) -> Decimal:
    if count == 0:
        return Decimal(0)
    return (total / count).quantize(MONEY_PRECISION)


def _revenue_per_hour(revenue: Decimal, slot_minutes: int) -> Decimal:
    if slot_minutes == 0:
        return Decimal(0)
    return (revenue / (Decimal(slot_minutes) / Decimal(60))).quantize(
        MONEY_PRECISION
    )


def _completed(bookings: list[Booking]) -> list[Booking]:
    return [booking for booking in bookings if booking.status == BookingStatus.COMPLETED]


def _build_revenue_report(
    bookings: list[Booking],
    previous_bookings: list[Booking],
    services: dict[object, Service],
    staff: dict[object, Staff],
    tz: ZoneInfo,
) -> RevenueReport:
    completed = _completed(bookings)
    previous_completed = _completed(previous_bookings)

    total_revenue = sum((booking.price for booking in completed), Decimal(0))
    previous_total = sum((booking.price for booking in previous_completed), Decimal(0))
    average_ticket = _average(total_revenue, len(completed))
    previous_average_ticket = _average(previous_total, len(previous_completed))

    daily_revenue: dict[date, Decimal] = defaultdict(Decimal)
    daily_count: Counter[date] = Counter()
    for booking in completed:
        local_date = booking.start_at.astimezone(tz).date()
        daily_revenue[local_date] += booking.price
        daily_count[local_date] += 1

    daily = [
        RevenueDay(
            date=local_date,
            revenue=daily_revenue[local_date],
            completed_bookings=daily_count[local_date],
        )
        for local_date in sorted(daily_revenue)
    ]

    def breakdown(
        items: list[Booking],
        name_for,
        id_for,
    ) -> list[RevenueBreakdown]:
        groups: dict[object, list[Booking]] = defaultdict(list)
        for booking in items:
            groups[id_for(booking)].append(booking)

        result = []
        for object_id, group in groups.items():
            revenue = sum((booking.price for booking in group), Decimal(0))
            result.append(
                RevenueBreakdown(
                    id=object_id,
                    name=name_for(object_id),
                    revenue=revenue,
                    completed_bookings=len(group),
                    average_ticket=_average(revenue, len(group)),
                )
            )
        result.sort(key=lambda item: (-item.revenue, item.name))
        return result

    return RevenueReport(
        total_revenue=total_revenue,
        completed_bookings=len(completed),
        average_ticket=average_ticket,
        previous_total_revenue=previous_total,
        previous_average_ticket=previous_average_ticket,
        revenue_change_percent=_change_percent(total_revenue, previous_total),
        average_ticket_change_percent=_change_percent(
            average_ticket, previous_average_ticket
        ),
        daily=daily,
        by_service=breakdown(
            completed,
            lambda service_id: services[service_id].name
            if service_id in services
            else "Servicio eliminado",
            lambda booking: booking.service_id,
        ),
        by_staff=breakdown(
            completed,
            lambda staff_id: staff[staff_id].display_name
            if staff_id in staff
            else "Empleado eliminado",
            lambda booking: booking.staff_id,
        ),
    )


def _build_occupancy_report(
    business: Business,
    staff_list: list[Staff],
    bookings: list[Booking],
    blocked_periods,
    date_from: date,
    date_to: date,
    tz: ZoneInfo,
) -> OccupancyReport:
    active_staff = [member for member in staff_list if member.is_active]
    applicable_blocks: dict[object, list[tuple[datetime, datetime]]] = {}
    for member in active_staff:
        applicable_blocks[member.id] = [
            (block.starts_at.astimezone(tz), block.ends_at.astimezone(tz))
            for block in blocked_periods
            if block.staff_id is None or block.staff_id == member.id
        ]

    bookings_by_staff: dict[object, list[Booking]] = defaultdict(list)
    for booking in bookings:
        if booking.status not in CANCELLED_STATUSES:
            bookings_by_staff[booking.staff_id].append(booking)

    daily_available: Counter[date] = Counter()
    daily_booked: Counter[date] = Counter()
    daily_no_show: Counter[date] = Counter()
    staff_rows: list[OccupancyStaff] = []

    for member in active_staff:
        available_total = 0
        booked_total = 0
        no_show_total = 0
        member_bookings = bookings_by_staff.get(member.id, [])

        for day in _iter_dates(date_from, date_to):
            schedule_intervals = _schedule_intervals(business, member, day, tz)
            available_intervals = _subtract_intervals(
                schedule_intervals, applicable_blocks.get(member.id, [])
            )
            available_minutes = _sum_minutes(available_intervals)

            booked_minutes = 0.0
            no_show_minutes = 0.0
            for booking in member_bookings:
                local_start = booking.start_at.astimezone(tz)
                local_end = booking.end_at.astimezone(tz)
                if local_end.date() < day or local_start.date() > day:
                    continue
                minutes = _intersection_minutes(
                    local_start, local_end, available_intervals
                )
                if minutes <= 0:
                    continue
                booked_minutes += minutes
                if booking.status == BookingStatus.NO_SHOW:
                    no_show_minutes += minutes

            booked = round(booked_minutes)
            no_show = round(no_show_minutes)
            available_total += available_minutes
            booked_total += booked
            no_show_total += no_show
            daily_available[day] += available_minutes
            daily_booked[day] += booked
            daily_no_show[day] += no_show

        staff_rows.append(
            OccupancyStaff(
                id=member.id,
                name=member.display_name,
                available_minutes=available_total,
                booked_minutes=booked_total,
                no_show_minutes=no_show_total,
                occupancy_rate=_percentage(booked_total, available_total),
            )
        )

    available_total = sum(daily_available.values())
    booked_total = sum(daily_booked.values())
    staff_rows.sort(key=lambda item: (-item.occupancy_rate, item.name))

    return OccupancyReport(
        available_minutes=available_total,
        booked_minutes=booked_total,
        idle_minutes=max(available_total - booked_total, 0),
        no_show_minutes=sum(daily_no_show.values()),
        occupancy_rate=_percentage(booked_total, available_total),
        by_staff=staff_rows,
        daily=[
            OccupancyDay(
                date=day,
                available_minutes=daily_available[day],
                booked_minutes=daily_booked[day],
                no_show_minutes=daily_no_show[day],
                occupancy_rate=_percentage(
                    daily_booked[day], daily_available[day]
                ),
            )
            for day in _iter_dates(date_from, date_to)
        ],
    )


def _build_profitability_report(
    bookings: list[Booking], services: dict[object, Service]
) -> ProfitabilityReport:
    completed = _completed(bookings)
    groups: dict[object, dict[str, object]] = defaultdict(
        lambda: {"revenue": Decimal(0), "slot_minutes": 0.0, "count": 0}
    )

    total_revenue = Decimal(0)
    total_slot_minutes = 0.0
    for booking in completed:
        service = services.get(booking.service_id)
        buffer_minutes = service.buffer_minutes if service else 0
        actual_minutes = max(
            (booking.end_at - booking.start_at).total_seconds() / 60, 0
        )
        slot_minutes = actual_minutes + buffer_minutes
        group = groups[booking.service_id]
        group["revenue"] = group["revenue"] + booking.price  # type: ignore[operator]
        group["slot_minutes"] = group["slot_minutes"] + slot_minutes  # type: ignore[operator]
        group["count"] = group["count"] + 1  # type: ignore[operator]
        total_revenue += booking.price
        total_slot_minutes += slot_minutes

    rows: list[ServiceProfitability] = []
    for service_id, group in groups.items():
        service = services.get(service_id)
        revenue = group["revenue"]
        slot_minutes = round(group["slot_minutes"])  # type: ignore[arg-type]
        rows.append(
            ServiceProfitability(
                id=service_id,
                name=service.name if service else "Servicio eliminado",
                duration_minutes=service.duration_minutes if service else 0,
                buffer_minutes=service.buffer_minutes if service else 0,
                completed_bookings=group["count"],  # type: ignore[arg-type]
                revenue=revenue,  # type: ignore[arg-type]
                slot_minutes=slot_minutes,
                revenue_per_hour=_revenue_per_hour(revenue, slot_minutes),  # type: ignore[arg-type]
            )
        )
    rows.sort(key=lambda item: (-item.revenue_per_hour, item.name))

    total_slot = round(total_slot_minutes)
    return ProfitabilityReport(
        revenue=total_revenue,
        slot_minutes=total_slot,
        revenue_per_hour=_revenue_per_hour(total_revenue, total_slot),
        by_service=rows,
    )


def _waitlist_group(
    entries: list[Waitlist],
    key: str,
    name: str,
    services: dict[object, Service],
) -> WaitlistBreakdown:
    statuses = Counter(entry.status.value for entry in entries)
    total = len(entries)
    booked = statuses.get(WaitlistStatus.BOOKED.value, 0)
    estimated_value = sum(
        (
            services[entry.service_id].price
            for entry in entries
            if entry.service_id is not None and entry.service_id in services
        ),
        Decimal(0),
    )

    return WaitlistBreakdown(
        id=key,  # type: ignore[arg-type]
        name=name,
        total=total,
        waiting=statuses.get(WaitlistStatus.WAITING.value, 0),
        offered=statuses.get(WaitlistStatus.OFFERED.value, 0),
        booked=booked,
        expired=statuses.get(WaitlistStatus.EXPIRED.value, 0),
        cancelled=statuses.get(WaitlistStatus.CANCELLED.value, 0),
        conversion_rate=_percentage(booked, total),
        estimated_value=estimated_value,
    )


def _build_waitlist_report(
    entries: list[Waitlist],
    services: dict[object, Service],
    staff: dict[object, Staff],
) -> WaitlistReport:
    status_counts = Counter(entry.status.value for entry in entries)
    total = len(entries)
    booked = status_counts.get(WaitlistStatus.BOOKED.value, 0)
    expired = status_counts.get(WaitlistStatus.EXPIRED.value, 0)
    cancelled = status_counts.get(WaitlistStatus.CANCELLED.value, 0)

    def grouped(key: str, names: dict[object, str], fallback: str) -> list[WaitlistBreakdown]:
        groups: dict[object | None, list[Waitlist]] = defaultdict(list)
        for entry in entries:
            groups[getattr(entry, key)].append(entry)

        rows = []
        for object_id, group in groups.items():
            name = fallback if object_id is None else names.get(object_id, "Eliminado")
            rows.append(_waitlist_group(group, object_id, name, services))  # type: ignore[arg-type]
        rows.sort(key=lambda item: (-item.total, item.name))
        return rows

    estimated_value = sum(
        (
            services[entry.service_id].price
            for entry in entries
            if entry.service_id is not None and entry.service_id in services
        ),
        Decimal(0),
    )
    estimated_converted_value = sum(
        (
            services[entry.service_id].price
            for entry in entries
            if entry.status == WaitlistStatus.BOOKED
            and entry.service_id is not None
            and entry.service_id in services
        ),
        Decimal(0),
    )

    return WaitlistReport(
        total_entries=total,
        by_status={
            state.value: status_counts.get(state.value, 0)
            for state in WaitlistStatus
        },
        conversion_rate=_percentage(booked, total),
        lost_rate=_percentage(expired + cancelled, total),
        estimated_value=estimated_value,
        estimated_converted_value=estimated_converted_value,
        by_service=grouped(
            "service_id",
            {service_id: service.name for service_id, service in services.items()},
            "Sin servicio",
        ),
        by_staff=grouped(
            "staff_id",
            {staff_id: member.display_name for staff_id, member in staff.items()},
            "Sin empleado",
        ),
    )


def _customer_name(
    customer_id: object, history: list[Booking], users: dict[object, User]
) -> str:
    user = users.get(customer_id)
    if user is not None:
        return user.full_name
    for booking in reversed(history):
        if booking.customer_name:
            return booking.customer_name
    return "Cliente"


def _customer_summary(
    customer_id: object,
    history: list[Booking],
    users: dict[object, User],
) -> CustomerSummary:
    completed_revenue = sum(
        (booking.price for booking in history if booking.status == BookingStatus.COMPLETED),
        Decimal(0),
    )
    last_visit = max((booking.start_at for booking in history), default=None)
    return CustomerSummary(
        id=customer_id,
        name=_customer_name(customer_id, history, users),
        visits=len(history),
        completed_revenue=completed_revenue,
        last_visit=last_visit,
    )


def _build_customer_report(
    bookings: list[Booking],
    start: datetime,
    end: datetime,
    users: dict[object, User],
) -> CustomerReport:
    history_by_customer: dict[object, list[Booking]] = defaultdict(list)
    for booking in bookings:
        if booking.status in CUSTOMER_STATUSES:
            history_by_customer[booking.customer_id].append(booking)

    for history in history_by_customer.values():
        history.sort(key=lambda booking: booking.start_at)

    period_by_customer: dict[object, list[Booking]] = defaultdict(list)
    for customer_id, history in history_by_customer.items():
        period_by_customer[customer_id] = [
            booking for booking in history if start <= booking.start_at < end
        ]

    active_ids = {
        customer_id
        for customer_id, period in period_by_customer.items()
        if period
    }
    prior_ids = {
        customer_id
        for customer_id, history in history_by_customer.items()
        if history and history[0].start_at < start
    }
    returning_ids = active_ids & prior_ids
    new_ids = active_ids - prior_ids
    inactive_ids = prior_ids - active_ids
    repeat_count = sum(
        1 for customer_id in active_ids if len(period_by_customer[customer_id]) >= 2
    )

    visits_in_period = sum(
        len(period_by_customer[customer_id]) for customer_id in active_ids
    )
    gaps: list[float] = []
    for history in history_by_customer.values():
        for previous, current in pairwise(history):
            gaps.append(
                max(
                    (current.start_at - previous.start_at).total_seconds()
                    / 86400,
                    0,
                )
            )

    top_customers = sorted(
        (
            _customer_summary(customer_id, period_by_customer[customer_id], users)
            for customer_id in active_ids
        ),
        key=lambda item: (-item.visits, -item.completed_revenue, item.name),
    )[:5]
    inactive_customers = sorted(
        (
            _customer_summary(customer_id, history_by_customer[customer_id], users)
            for customer_id in inactive_ids
        ),
        key=lambda item: item.last_visit or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )[:5]

    return CustomerReport(
        active_customers=len(active_ids),
        new_customers=len(new_ids),
        returning_customers=len(returning_ids),
        repeat_customers=repeat_count,
        inactive_customers_count=len(inactive_ids),
        new_customer_rate=_percentage(len(new_ids), len(active_ids)),
        repeat_rate=_percentage(repeat_count, len(active_ids)),
        retention_rate=_percentage(len(returning_ids), len(prior_ids))
        if prior_ids
        else None,
        average_visits_per_customer=round(visits_in_period / len(active_ids), 1)
        if active_ids
        else 0.0,
        average_days_between_visits=round(sum(gaps) / len(gaps), 1)
        if gaps
        else None,
        top_customers=top_customers,
        inactive_customers=inactive_customers,
    )


async def get_business_reports(
    user: User,
    business_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> BusinessReports:
    """Calcula todos los reportes del negocio para el periodo indicado."""
    business = await get_managed_business(business_id, user)
    tz = ZoneInfo(business.timezone)

    date_from, date_to, start, end = _resolve_range(date_from, date_to, tz)
    previous_from, previous_to = _previous_range(date_from, date_to)
    previous_start, previous_end = _range_bounds(previous_from, previous_to, tz)

    period_bookings = await booking_repository.find_many(
        {"business_id": business.id, "start_at": {"$gte": start, "$lt": end}}
    )
    previous_bookings = await booking_repository.find_many(
        {
            "business_id": business.id,
            "start_at": {"$gte": previous_start, "$lt": previous_end},
        }
    )
    occupancy_bookings = await booking_repository.find_many(
        {
            "business_id": business.id,
            "start_at": {"$lt": end},
            "end_at": {"$gt": start},
        }
    )
    customer_bookings = await booking_repository.find_many(
        {
            "business_id": business.id,
            "status": {"$ne": BookingStatus.CANCELLED},
            "start_at": {"$lt": end},
        }
    )
    services = await service_repository.find_many({"business_id": business.id})
    staff = await staff_repository.find_many({"business_id": business.id})
    blocked_periods = await blocked_period_repository.find_many(
        {
            "business_id": business.id,
            "starts_at": {"$lt": end},
            "ends_at": {"$gt": start},
        }
    )
    waitlist_entries = await waitlist_repository.find_many(
        {
            "business_id": business.id,
            "created_at": {"$gte": start, "$lt": end},
        }
    )

    services_by_id = {service.id: service for service in services}
    staff_by_id = {member.id: member for member in staff}

    customer_ids = {
        booking.customer_id
        for booking in customer_bookings
        if booking.status in CUSTOMER_STATUSES
    }
    users = (
        await user_repository.find_many({"_id": {"$in": list(customer_ids)}})
        if customer_ids
        else []
    )
    users_by_id = {customer.id: customer for customer in users}

    return BusinessReports(
        date_from=date_from,
        date_to=date_to,
        timezone=business.timezone,
        currency=business.currency,
        revenue=_build_revenue_report(
            period_bookings, previous_bookings, services_by_id, staff_by_id, tz
        ),
        occupancy=_build_occupancy_report(
            business,
            staff,
            occupancy_bookings,
            blocked_periods,
            date_from,
            date_to,
            tz,
        ),
        profitability=_build_profitability_report(
            period_bookings, services_by_id
        ),
        waitlist=_build_waitlist_report(
            waitlist_entries, services_by_id, staff_by_id
        ),
        customers=_build_customer_report(
            customer_bookings, start, end, users_by_id
        ),
    )
