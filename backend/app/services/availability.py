"""Motor de disponibilidad: cálculo de huecos libres.

Combina el horario efectivo (del empleado si lo tiene, si no del negocio), la
duración y el margen del servicio, y los intervalos ocupados (reservas no
canceladas y periodos bloqueados) para obtener los huecos reservables.

La lógica pura (`compute_free_slots`, `overlaps`, `schedule_for_date`) no toca
la base de datos, lo que la hace fácil de probar. `collect_busy_intervals` es la
parte que consulta MongoDB.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.db.repositories import blocked_period_repository, booking_repository
from app.models import (
    BookingStatus,
    Business,
    DaySchedule,
    Service,
    Staff,
    WeeklySchedule,
)

# Granularidad con la que se ofrecen horas de inicio (cada cuántos minutos).
DEFAULT_SLOT_STEP_MINUTES = 15

# Estados de reserva que ocupan agenda.
BUSY_BOOKING_STATUSES = [BookingStatus.PENDING, BookingStatus.CONFIRMED]


def effective_schedule(business: Business, staff: Staff | None) -> WeeklySchedule:
    """Devuelve el horario aplicable: el del empleado si lo define, si no el del negocio."""
    if staff is not None and staff.schedule is not None:
        return staff.schedule
    return business.schedule


def schedule_for_date(
    business: Business, staff: Staff | None, target_date: date
) -> DaySchedule | None:
    """Devuelve el horario del día de la semana indicado, o `None` si no existe."""
    schedule = effective_schedule(business, staff)
    weekday = target_date.weekday()
    for day in schedule.days:
        if day.weekday == weekday:
            return day
    return None


def overlaps(start: datetime, end: datetime, intervals: list[tuple[datetime, datetime]]) -> bool:
    """Indica si el rango `[start, end)` se solapa con alguno de los intervalos."""
    return any(interval_start < end and start < interval_end for interval_start, interval_end in intervals)


def compute_free_slots(
    business: Business,
    staff: Staff | None,
    service: Service,
    target_date: date,
    busy: list[tuple[datetime, datetime]],
    step_minutes: int = DEFAULT_SLOT_STEP_MINUTES,
) -> list[tuple[datetime, datetime]]:
    """Calcula los huecos libres para un servicio en una fecha concreta.

    Recorre cada franja del día en pasos de `step_minutes` y conserva las horas
    de inicio donde el servicio (más su margen) cabe sin solaparse con `busy`.

    Args:
        business: Negocio (aporta zona horaria y horario por defecto).
        staff: Empleado (aporta su horario si lo tiene). Puede ser `None`.
        service: Servicio (aporta duración y margen).
        target_date: Fecha local del negocio a evaluar.
        busy: Intervalos ocupados (reservas y bloqueos), en UTC.
        step_minutes: Granularidad de los posibles inicios.

    Returns:
        Lista de tuplas `(inicio, fin)` en la zona horaria del negocio.
    """
    tz = ZoneInfo(business.timezone)
    day = schedule_for_date(business, staff, target_date)
    if day is None or day.is_closed:
        return []

    duration = timedelta(minutes=service.duration_minutes)
    buffer = timedelta(minutes=service.buffer_minutes)
    step = timedelta(minutes=step_minutes)

    slots: list[tuple[datetime, datetime]] = []
    for interval in day.intervals:
        open_dt = datetime.combine(target_date, interval.open, tzinfo=tz)
        close_dt = datetime.combine(target_date, interval.close, tzinfo=tz)
        candidate = open_dt
        while candidate + duration <= close_dt:
            slot_end = candidate + duration
            occupied_end = slot_end + buffer
            if not overlaps(candidate, occupied_end, busy):
                slots.append((candidate, slot_end))
            candidate += step
    return slots


async def collect_busy_intervals(
    business_id: object,
    staff_id: object | None,
    range_start: datetime,
    range_end: datetime,
) -> list[tuple[datetime, datetime]]:
    """Reúne los intervalos ocupados que tocan el rango dado.

    Incluye reservas activas del empleado y periodos bloqueados que afectan al
    negocio o al empleado concreto.
    """
    booking_filter: dict[str, object] = {
        "business_id": business_id,
        "status": {"$in": BUSY_BOOKING_STATUSES},
        "start_at": {"$lt": range_end},
        "end_at": {"$gt": range_start},
    }
    if staff_id is not None:
        booking_filter["staff_id"] = staff_id

    bookings = await booking_repository.find_many(booking_filter)

    block_filter: dict[str, object] = {
        "business_id": business_id,
        "starts_at": {"$lt": range_end},
        "ends_at": {"$gt": range_start},
    }
    if staff_id is not None:
        # Bloqueos de todo el negocio (`staff_id` nulo) o del empleado concreto.
        block_filter["staff_id"] = {"$in": [staff_id, None]}

    blocks = await blocked_period_repository.find_many(block_filter)

    intervals = [(booking.start_at, booking.end_at) for booking in bookings]
    intervals.extend((block.starts_at, block.ends_at) for block in blocks)
    return intervals


async def day_availability(
    business: Business,
    service: Service,
    staff: Staff,
    target_date: date,
    step_minutes: int = DEFAULT_SLOT_STEP_MINUTES,
) -> list[tuple[datetime, datetime]]:
    """Calcula los huecos libres de un empleado para un servicio en una fecha."""
    tz = ZoneInfo(business.timezone)
    day_start = datetime.combine(target_date, time(0, 0), tzinfo=tz).astimezone(UTC)
    day_end = day_start + timedelta(days=1)

    busy = await collect_busy_intervals(business.id, staff.id, day_start, day_end)
    return compute_free_slots(business, staff, service, target_date, busy, step_minutes)
