"""Lógica de negocio del dashboard de estadísticas de un negocio.

Solo accesible para quien gestiona el negocio. Calcula, sobre un rango de fechas
opcional (por defecto, todo el histórico): número de reservas por estado, los
ingresos de las completadas y los servicios/empleados más reservados.
"""

from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import NamedTuple
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app.db.repositories import (
    booking_repository,
    service_repository,
    staff_repository,
)
from app.models import Booking, BookingStatus, Business, User
from app.schemas.stats import BusinessStats, StatsItem
from app.services.business import get_managed_business

# Máximo de elementos devueltos en cada ranking.
TOP_LIMIT = 5


class _Aggregates(NamedTuple):
    """Resultado intermedio del cálculo sobre las reservas."""

    total: int
    by_status: dict[str, int]
    revenue: Decimal
    services: Counter
    staff: Counter


def _range_bounds(
    date_from: date | None, date_to: date | None, tz: ZoneInfo
) -> tuple[datetime | None, datetime | None]:
    """Convierte un rango de fechas locales a límites UTC semiabiertos.

    Si no se indica ninguna fecha, devuelve `(None, None)` para no filtrar.
    """
    if date_from is None and date_to is None:
        return None, None

    if date_from and date_to and date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="`date_to` no puede ser anterior a `date_from`",
        )

    start = None
    if date_from is not None:
        start = datetime.combine(date_from, time(0, 0), tzinfo=tz).astimezone(UTC)

    end = None
    if date_to is not None:
        end = datetime.combine(
            date_to + timedelta(days=1), time(0, 0), tzinfo=tz
        ).astimezone(UTC)

    return start, end


def _booking_filter(business: Business, start: datetime | None, end: datetime | None) -> dict:
    """Construye el filtro de reservas del negocio acotado por fecha si procede."""
    filters: dict = {"business_id": business.id}
    if start is not None or end is not None:
        date_range: dict = {}
        if start is not None:
            date_range["$gte"] = start
        if end is not None:
            date_range["$lt"] = end
        filters["start_at"] = date_range
    return filters


def _aggregate(bookings: list[Booking]) -> _Aggregates:
    """Calcula los contadores y los ingresos a partir de las reservas."""
    by_status: Counter = Counter(booking.status.value for booking in bookings)

    revenue = sum(
        (booking.price for booking in bookings if booking.status == BookingStatus.COMPLETED),
        Decimal(0),
    )

    active = [booking for booking in bookings if booking.status != BookingStatus.CANCELLED]
    return _Aggregates(
        total=len(bookings),
        by_status={state.value: by_status.get(state.value, 0) for state in BookingStatus},
        revenue=revenue,
        services=Counter(booking.service_id for booking in active),
        staff=Counter(booking.staff_id for booking in active),
    )


def _top_items(counter: Counter, names: dict, limit: int = TOP_LIMIT) -> list[StatsItem]:
    """Convierte un contador {id: nº} en un ranking ordenado y acotado."""
    ordered = sorted(counter.items(), key=lambda item: (-item[1], names.get(item[0], "")))
    return [
        StatsItem(id=object_id, name=names.get(object_id, ""), count=count)
        for object_id, count in ordered[:limit]
    ]


async def _resolve_names(repository, ids: list, attribute: str) -> dict:
    """Resuelve `{id: nombre}` para los documentos indicados."""
    if not ids:
        return {}
    documents = await repository.find_many({"_id": {"$in": ids}})
    return {document.id: getattr(document, attribute) for document in documents}


async def get_business_stats(
    user: User, business_id: str, date_from: date | None = None, date_to: date | None = None
) -> BusinessStats:
    """Devuelve el dashboard de estadísticas de un negocio gestionable."""
    business = await get_managed_business(business_id, user)
    start, end = _range_bounds(date_from, date_to, ZoneInfo(business.timezone))

    bookings = await booking_repository.find_many(_booking_filter(business, start, end))
    aggregates = _aggregate(bookings)

    service_names = await _resolve_names(service_repository, list(aggregates.services), "name")
    staff_names = await _resolve_names(staff_repository, list(aggregates.staff), "display_name")

    return BusinessStats(
        total_bookings=aggregates.total,
        bookings_by_status=aggregates.by_status,
        revenue_completed=aggregates.revenue,
        currency=business.currency,
        top_services=_top_items(aggregates.services, service_names),
        top_staff=_top_items(aggregates.staff, staff_names),
    )
