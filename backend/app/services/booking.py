"""Lógica de negocio de las reservas (booking).

La creación valida todo el flujo: el negocio y el servicio están activos, el
empleado ofrece el servicio y la hora solicitada cae dentro del horario y no se
solapa con reservas ni bloqueos. Los clientes reservan para sí mismos; los
propietarios gestionan todas las reservas de su negocio.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from pymongo import ASCENDING, DESCENDING

from app.core.plans import assert_within_limit, limits_for
from app.db.repositories import (
    booking_repository,
    business_repository,
    service_repository,
    staff_repository,
)
from app.models import Booking, BookingStatus, Business, Service, Staff, User, UserRole
from app.models.types import validate_object_id
from app.schemas.booking import (
    AvailabilityResponse,
    AvailabilitySlot,
    BookingCreate,
    BookingStatusUpdate,
)
from app.services.availability import (
    collect_busy_intervals,
    day_availability,
    overlaps,
    schedule_for_date,
)
from app.services.business import get_managed_business
from app.services.waitlist import offer_freed_slot


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


async def _get_active_business(business_id: str) -> Business:
    """Carga un negocio activo (sin exigir propiedad: los clientes reservan)."""
    try:
        object_id = validate_object_id(business_id)
    except ValueError as exc:
        raise _not_found("Negocio no encontrado") from exc

    business = await business_repository.get_by_id(object_id)
    if business is None or not business.is_active:
        raise _not_found("Negocio no encontrado")
    return business


async def _get_active_service(business_id: object, service_id: object) -> Service:
    """Carga un servicio activo del negocio."""
    try:
        service = await service_repository.find_one(
            {"_id": validate_object_id(service_id), "business_id": business_id, "is_active": True}
        )
    except ValueError as exc:
        raise _unprocessable("Servicio no válido") from exc
    if service is None:
        raise _unprocessable("Servicio no válido")
    return service


async def _get_active_staff(business_id: object, staff_id: object) -> Staff:
    """Carga un empleado activo del negocio."""
    try:
        staff = await staff_repository.find_one(
            {"_id": validate_object_id(staff_id), "business_id": business_id, "is_active": True}
        )
    except ValueError as exc:
        raise _unprocessable("Empleado no válido") from exc
    if staff is None:
        raise _unprocessable("Empleado no válido")
    return staff


async def _assert_bookable(
    business: Business, staff: Staff, service: Service, start_at: datetime
) -> None:
    """Comprueba que el servicio puede reservarse a esa hora.

    Verifica: hora futura, dentro del horario del día y sin solapamiento con
    reservas o bloqueos existentes.
    """
    tz = ZoneInfo(business.timezone)
    start_local = start_at.astimezone(tz)
    target_date = start_local.date()

    if start_at <= datetime.now(UTC):
        raise _conflict("La reserva debe ser en el futuro")

    day = schedule_for_date(business, staff, target_date)
    if day is None or day.is_closed:
        raise _conflict("El negocio está cerrado ese día")

    duration = timedelta(minutes=service.duration_minutes)
    start_naive = start_local.replace(tzinfo=None)
    end_naive = start_naive + duration

    fits = any(
        datetime.combine(target_date, interval.open) <= start_naive
        and end_naive <= datetime.combine(target_date, interval.close)
        for interval in day.intervals
    )
    if not fits:
        raise _conflict("La hora está fuera del horario de atención")

    day_start = datetime.combine(target_date, time(0, 0), tzinfo=tz).astimezone(UTC)
    day_end = day_start + timedelta(days=1)
    busy = await collect_busy_intervals(business.id, staff.id, day_start, day_end)
    if overlaps(start_at, start_at + duration + timedelta(minutes=service.buffer_minutes), busy):
        raise _conflict("Ese horario ya está ocupado")


async def get_availability(
    business_id: str, service_id: str, staff_id: str, target_date
) -> AvailabilityResponse:
    """Calcula los huecos libres de un empleado para un servicio en una fecha.

    No exige propiedad del negocio: cualquier usuario puede consultar
    disponibilidad para reservar.
    """
    business = await _get_active_business(business_id)
    service = await _get_active_service(business.id, service_id)
    staff = await _get_active_staff(business.id, staff_id)

    if service.id not in staff.services:
        raise _unprocessable("El empleado no ofrece este servicio")

    now = datetime.now(UTC)
    slots = await day_availability(business, service, staff, target_date)
    return AvailabilityResponse(
        date=target_date,
        timezone=business.timezone,
        service_id=service.id,
        staff_id=staff.id,
        slots=[
            AvailabilitySlot(start_at=start, end_at=end)
            for start, end in slots
            if start.astimezone(UTC) > now
        ],
    )


async def _count_bookings_this_month(business_id: object) -> int:
    """Cuenta las reservas del negocio con inicio dentro del mes actual (UTC)."""
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    return await booking_repository.count(
        {"business_id": business_id, "start_at": {"$gte": month_start, "$lt": next_month}}
    )


async def create_booking(user: User, business_id: str, payload: BookingCreate) -> Booking:
    """Crea una reserva para el usuario autenticado."""
    business = await _get_active_business(business_id)

    current = await _count_bookings_this_month(business.id)
    assert_within_limit(
        current,
        limits_for(business.plan).max_bookings_per_month,
        "reservas al mes",
        business.plan,
    )

    service = await _get_active_service(business.id, payload.service_id)
    staff = await _get_active_staff(business.id, payload.staff_id)

    if service.id not in staff.services:
        raise _unprocessable("El empleado no ofrece este servicio")

    await _assert_bookable(business, staff, service, payload.start_at)

    start_at = payload.start_at.astimezone(UTC)
    end_at = start_at + timedelta(minutes=service.duration_minutes)

    booking = Booking(
        business_id=business.id,
        staff_id=staff.id,
        service_id=service.id,
        customer_id=user.id,
        start_at=start_at,
        end_at=end_at,
        status=BookingStatus.PENDING,
        price=service.price,
        currency=business.currency,
        customer_name=user.full_name,
        customer_phone=user.phone,
        notes=payload.notes,
    )
    return await booking_repository.insert(booking)


async def list_business_bookings(
    user: User,
    business_id: str,
    *,
    status: BookingStatus | None = None,
    staff_id: str | None = None,
    service_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 0,
) -> list[Booking]:
    """Lista las reservas de un negocio gestionable con filtros y paginación.

    Los filtros por fechas se interpretan en la zona horaria del negocio.
    """
    business = await get_managed_business(business_id, user)
    tz = ZoneInfo(business.timezone)

    query: dict[str, object] = {"business_id": business.id}

    if status is not None:
        query["status"] = status
    if staff_id is not None:
        try:
            query["staff_id"] = validate_object_id(staff_id)
        except ValueError as exc:
            raise _not_found("Empleado no encontrado") from exc
    if service_id is not None:
        try:
            query["service_id"] = validate_object_id(service_id)
        except ValueError as exc:
            raise _not_found("Servicio no encontrado") from exc
    if date_from is not None or date_to is not None:
        date_range: dict[str, object] = {}
        if date_from is not None:
            start = datetime.combine(date_from, time(0, 0), tzinfo=tz).astimezone(UTC)
            date_range["$gte"] = start
        if date_to is not None:
            end = datetime.combine(date_to + timedelta(days=1), time(0, 0), tzinfo=tz).astimezone(UTC)
            date_range["$lt"] = end
        query["start_at"] = date_range
        if date_from is not None and date_to is not None and date_to < date_from:
            raise _unprocessable("`date_to` no puede ser anterior a `date_from`")

    return await booking_repository.find_many(
        query, sort=[("start_at", ASCENDING)], skip=skip, limit=limit
    )


async def list_my_bookings(user: User) -> list[Booking]:
    """Lista las reservas del usuario como cliente."""
    return await booking_repository.find_many(
        {"customer_id": user.id}, sort=[("start_at", DESCENDING)]
    )


async def _get_booking_in_business(booking_id: object, business_id: object) -> Booking:
    """Carga una reserva asegurando que pertenece al negocio indicado."""
    try:
        object_id = validate_object_id(booking_id)
    except ValueError as exc:
        raise _not_found("Reserva no encontrada") from exc

    booking = await booking_repository.find_one({"_id": object_id, "business_id": business_id})
    if booking is None:
        raise _not_found("Reserva no encontrada")
    return booking


def _is_manager(user: User, business: Business) -> bool:
    """Indica si el usuario gestiona el negocio (propietario o admin)."""
    return user.role == UserRole.ADMIN or business.owner_id == user.id


async def get_booking(user: User, business_id: str, booking_id: str) -> Booking:
    """Devuelve una reserva al gestor del negocio o al cliente que la hizo."""
    business = await _get_active_business(business_id)
    booking = await _get_booking_in_business(booking_id, business.id)
    if not _is_manager(user, business) and booking.customer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta reserva",
        )
    return booking


async def update_booking_status(
    user: User, business_id: str, booking_id: str, payload: BookingStatusUpdate
) -> Booking:
    """Cambia el estado de una reserva.

    El gestor puede asignar cualquier estado; el cliente solo puede cancelar su
    propia reserva.
    """
    business = await _get_active_business(business_id)
    booking = await _get_booking_in_business(booking_id, business.id)

    if not _is_manager(user, business):
        if booking.customer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta reserva",
            )
        if payload.status != BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes cancelar tu propia reserva",
            )

    changes: dict[str, object] = {"status": payload.status}
    if payload.cancellation_reason is not None:
        changes["cancellation_reason"] = payload.cancellation_reason

    updated = await booking_repository.update(booking.id, changes)
    if updated is None:  # pragma: no cover - la reserva existe, no debería ocurrir
        raise _not_found("Reserva no encontrada")

    if payload.status == BookingStatus.CANCELLED:
        await offer_freed_slot(business.id, booking)

    return updated


async def delete_booking(user: User, business_id: str, booking_id: str) -> None:
    """Elimina una reserva (solo gestores del negocio)."""
    business = await get_managed_business(business_id, user)
    booking = await _get_booking_in_business(booking_id, business.id)
    await booking_repository.delete(booking.id)
